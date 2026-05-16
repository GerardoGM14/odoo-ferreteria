# ERP Ferretería — Odoo 17

Solución ERP modular para ferreterías en Perú, desarrollada sobre **Odoo 17 Community** y desplegada con Docker. Incluye 7 módulos custom que cubren inventario, ventas, compras, facturación electrónica SUNAT, finanzas, gestión de usuarios e integración con el Punto de Venta.

---

## Tabla de contenidos

- [Stack](#stack)
- [Arquitectura](#arquitectura)
- [Módulos](#módulos)
- [Requisitos](#requisitos)
- [Puesta en marcha](#puesta-en-marcha)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Tests](#tests)
- [Backups](#backups)
- [Configuración](#configuración)
- [Licencia](#licencia)

---

## Stack

| Componente | Versión |
|---|---|
| Odoo | 17.0 Community |
| PostgreSQL | 15 |
| Python | 3 (base de la imagen `odoo:17.0`) |
| Dependencias Python extra | `openpyxl` |
| Orquestación | Docker Compose |

---

## Arquitectura

Despliegue de dos servicios definidos en [docker-compose.yml](docker-compose.yml):

- **web** — Imagen `odoo-ferreteria:17.0` construida desde [Dockerfile](Dockerfile) (Odoo 17 + `openpyxl`). Expone el puerto `8069`, monta `./addons` en `/mnt/extra-addons` y `./config` en `/etc/odoo`.
- **db** — PostgreSQL 15 con volumen persistente `odoo-db-data`.

Ambos servicios comparten la red bridge `odoo-network` y se reinician automáticamente (`restart: unless-stopped`).

---

## Módulos

Todos los módulos viven en [addons/](addons/) y siguen la convención de namespace `ferreteria_*`. Cada uno declara su propia capa de seguridad (`security/*.xml` + `ir.model.access.csv`) y vistas.

### 1. `ferreteria_inventario` — Inventario *(application)*

Base del ERP. Provee modelos y datos maestros que el resto de módulos consumen.

- Extensión de `product.template` con campos específicos de ferretería
- Categorías jerárquicas (`ferreteria.categoria`)
- Kardex de inventario en tiempo real
- Alertas de stock mínimo (con `ir.cron` configurado en `data/ferreteria_cron_data.xml`)
- 3 listas de precios precargadas (Mayorista, Normal, Menudeo)
- Grupos de seguridad base (Vendedor / Administrador)

**Depends:** `base`, `stock`, `product`, `sale_management`

### 2. `ferreteria_ventas` — Ventas

- Importación masiva de productos desde Excel (wizard + `openpyxl`)
- Extensión de cotizaciones y órdenes de venta
- Gestión de clientes con historial
- Descuentos autorizados por grupo de seguridad
- 4 listas de precios por volumen

**Depends:** `ferreteria_inventario`, `sale_management`, `contacts`

### 3. `ferreteria_compras` — Compras

- Proveedores con datos extendidos
- RFQ y órdenes de compra con actualización automática de stock
- `product.supplierinfo` extendido para comparación de precios
- Registro de proveedores por categoría
- Control de plazos de entrega

**Depends:** `ferreteria_inventario`, `purchase`

### 4. `ferreteria_facturacion` — Facturación Electrónica SUNAT (Perú)

- Comprobantes electrónicos: **Factura (01)**, **Boleta (03)**, **Nota de Crédito (07)**, **Nota de Débito (08)**
- Series y correlativos por tipo de documento
- Configuración SUNAT (entornos Beta/Producción)
- Generación de XML conforme a **UBL 2.1**
- Tipos de documento de identidad (RUC, DNI, CE, …)
- Tributos peruanos (IGV, ISC, otros)

**Depends:** `ferreteria_inventario`, `account`

### 5. `ferreteria_finanzas` — Finanzas

- Caja diaria: apertura, cierre y arqueo
- Movimientos de caja (ingresos, egresos, gastos)
- Cuentas por cobrar / por pagar
- Conciliación bancaria
- Reportes: ganancia diaria, flujo de caja, resumen financiero

**Depends:** `ferreteria_inventario`, `ferreteria_facturacion`, `account`

### 6. `ferreteria_usuarios` — Usuarios y Seguridad

- Perfiles predefinidos por área (ventas, almacén, caja, gerencia)
- Restricciones por módulo y funcionalidad
- Dashboard de actividad por usuario
- Control de sesiones activas

**Depends:** `ferreteria_inventario`, `ferreteria_ventas`, `ferreteria_compras`, `ferreteria_facturacion`, `ferreteria_finanzas`

### 7. `ferreteria_pos` — Integración Punto de Venta

Módulo puente entre los módulos custom y el POS estándar de Odoo.

- Sincroniza `ferreteria.categoria` ↔ `pos.category`
- Asigna automáticamente productos a su categoría POS al crearse/editarse
- Configura el POS con la lista de precios de ferretería por defecto (`post_init_hook`)
- Oculta el menú de Caja Diaria de `ferreteria_finanzas` para evitar duplicidad con la sesión del POS

**Depends:** `ferreteria_inventario`, `ferreteria_finanzas`, `point_of_sale`

### Grafo de dependencias

```
ferreteria_inventario  ← base de todos
        ↑
        ├── ferreteria_ventas
        ├── ferreteria_compras
        ├── ferreteria_facturacion
        │       ↑
        │       └── ferreteria_finanzas
        │               ↑
        │               └── ferreteria_pos
        └── ferreteria_usuarios (depende de todos los anteriores excepto POS)
```

---

## Requisitos

- Docker Desktop (Windows / macOS) o Docker Engine + Docker Compose (Linux)
- Git
- 4 GB de RAM libres recomendados
- Puerto `8069` libre

---

## Puesta en marcha

```bash
# 1. Clonar
git clone https://github.com/GerardoGM14/odoo-ferreteria.git
cd odoo-ferreteria

# 2. Levantar
docker compose up -d --build

# 3. Acceder
# http://localhost:8069
#   Master Password: admin   (definida en config/odoo.conf)
```

Al crear la base de datos, instala primero `ferreteria_inventario` y luego el resto en el orden que necesites — Odoo resolverá las dependencias.

Para detener:

```bash
docker compose down            # mantiene volúmenes
docker compose down -v         # elimina volúmenes (¡borra la BD!)
```

---

## Estructura del repositorio

```
odoo-ferreteria/
├── addons/                       # Módulos custom
│   ├── ferreteria_inventario/
│   ├── ferreteria_ventas/
│   ├── ferreteria_compras/
│   ├── ferreteria_facturacion/
│   ├── ferreteria_finanzas/
│   ├── ferreteria_usuarios/
│   └── ferreteria_pos/
├── config/
│   └── odoo.conf                 # Configuración del servidor Odoo
├── scripts/
│   └── backup.ps1                # Backup de BD + filestore (PowerShell)
├── data/                         # Volúmenes locales (gitignored)
├── historical/                   # Dumps y datos del cliente (gitignored)
├── Dockerfile                    # Odoo 17 + openpyxl
├── docker-compose.yml            # web + db
├── run_tests.sh                  # Runner de tests
└── README.md
```

---

## Tests

Ejecutar todos los tests:

```bash
./run_tests.sh
```

O un módulo en concreto:

```bash
./run_tests.sh inventario
./run_tests.sh ventas
./run_tests.sh compras
./run_tests.sh facturacion
./run_tests.sh finanzas
./run_tests.sh usuarios
```

El script crea una base `odoo_test`, instala los módulos con `--test-enable`, parsea el log buscando `FAIL`/`ERROR` y limpia la BD de prueba al terminar. Requiere los contenedores arriba.

---

## Backups

[scripts/backup.ps1](scripts/backup.ps1) genera un `.zip` que contiene:

- Dump binario de la BD (`pg_dump -Fc`)
- `tar.gz` del filestore

Uso por defecto (BD `ferreteria`, salida `./backups/`, retención de 14 backups):

```powershell
.\scripts\backup.ps1
```

Personalizado:

```powershell
.\scripts\backup.ps1 -BackupDir "D:\backups\odoo" -DbName "ferreteria" -KeepCount 30
```

Requiere los contenedores `web` y `db` corriendo. Rota automáticamente los backups antiguos.

---

## Configuración

[config/odoo.conf](config/odoo.conf) — credenciales y rutas:

```ini
[options]
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
data_dir    = /var/lib/odoo
admin_passwd = admin
db_host = db
db_user = odoo
db_password = odoo
db_port = 5432
```

> **Producción:** cambia `admin_passwd` y las credenciales de PostgreSQL (`POSTGRES_PASSWORD` en `docker-compose.yml` + `db_password` en `odoo.conf`) antes de exponer el servicio.

---

## Licencia

- **Repositorio:** [MIT](LICENSE)
- **Módulos Odoo:** LGPL-3 (declarado en cada `__manifest__.py`, requisito de la plataforma)

---

## Autor

Desarrollado por **Trigra** — <https://trigra.com.pe>
