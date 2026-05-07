# Backup de Odoo Ferreteria
#
# Ejecuta pg_dump de la BD y empaqueta el filestore desde los contenedores Docker.
# Genera un .zip con fecha y conserva los ultimos $KeepCount backups.
#
# Uso:
#   .\scripts\backup.ps1
#   .\scripts\backup.ps1 -BackupDir "D:\backups\odoo" -KeepCount 30

param(
    [string]$BackupDir = "$PSScriptRoot\..\backups",
    [string]$DbName    = "ferreteria",
    [int]$KeepCount    = 14
)

$ErrorActionPreference = "Stop"

# Resolver ruta del repo (dos carpetas arriba de scripts/)
$RepoDir = Resolve-Path "$PSScriptRoot\.."
Set-Location $RepoDir

# Asegurar carpeta de backups
$BackupDir = [System.IO.Path]::GetFullPath($BackupDir)
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$WorkDir   = Join-Path $env:TEMP "odoo-backup-$Timestamp"
New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Iniciando backup de $DbName"

try {
    # 1. Verificar contenedores arriba
    $running = docker compose ps --status running --services 2>$null
    if ($running -notcontains "db" -or $running -notcontains "web") {
        throw "Los contenedores db/web no estan corriendo. Ejecuta 'docker compose up -d' antes."
    }

    # 2. pg_dump dentro del contenedor db
    $DumpFile = Join-Path $WorkDir "$DbName.backup"
    Write-Host "  -> pg_dump"
    docker compose exec -T db pg_dump -U odoo -Fc -d $DbName -f /tmp/db.backup
    if ($LASTEXITCODE -ne 0) { throw "pg_dump fallo" }
    docker compose cp "db:/tmp/db.backup" $DumpFile
    docker compose exec -T db rm -f /tmp/db.backup | Out-Null

    # 3. tar del filestore desde el contenedor web
    $FilestoreTar = Join-Path $WorkDir "filestore.tar.gz"
    Write-Host "  -> filestore"
    docker compose exec -u 0 -T web tar -czf /tmp/filestore.tar.gz -C /var/lib/odoo/filestore $DbName
    if ($LASTEXITCODE -ne 0) { throw "tar del filestore fallo" }
    docker compose cp "web:/tmp/filestore.tar.gz" $FilestoreTar
    docker compose exec -u 0 -T web rm -f /tmp/filestore.tar.gz | Out-Null

    # 4. Empaquetar en un solo .zip
    $ZipPath = Join-Path $BackupDir "${DbName}_${Timestamp}.zip"
    Write-Host "  -> zip"
    Compress-Archive -Path "$WorkDir\*" -DestinationPath $ZipPath -CompressionLevel Optimal -Force

    $SizeMB = [math]::Round((Get-Item $ZipPath).Length / 1MB, 2)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] OK: $ZipPath ($SizeMB MB)"

    # 5. Rotacion: dejar solo los ultimos $KeepCount
    $old = Get-ChildItem -Path $BackupDir -Filter "${DbName}_*.zip" |
           Sort-Object LastWriteTime -Descending |
           Select-Object -Skip $KeepCount
    foreach ($f in $old) {
        Remove-Item $f.FullName -Force
        Write-Host "  rotado: $($f.Name)"
    }
}
finally {
    if (Test-Path $WorkDir) { Remove-Item $WorkDir -Recurse -Force }
}
