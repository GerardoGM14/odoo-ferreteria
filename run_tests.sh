#!/bin/bash
# =============================================================
# Script para ejecutar tests unitarios - ERP Ferretería
# =============================================================
# Uso:
#   ./run_tests.sh              → Ejecuta tests de TODOS los módulos
#   ./run_tests.sh inventario   → Solo tests de ferreteria_inventario
#   ./run_tests.sh ventas       → Solo tests de ferreteria_ventas
#   ./run_tests.sh compras      → Solo tests de ferreteria_compras
#   ./run_tests.sh facturacion  → Solo tests de ferreteria_facturacion
#   ./run_tests.sh finanzas     → Solo tests de ferreteria_finanzas
#   ./run_tests.sh usuarios     → Solo tests de ferreteria_usuarios
# =============================================================

set -e

DB_TEST="odoo_test"
CONTAINER="odoo-ferreteria-web-1"

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=============================================${NC}"
echo -e "${YELLOW}  ERP Ferretería - Ejecución de Tests${NC}"
echo -e "${YELLOW}=============================================${NC}"

# Verificar que Docker está corriendo
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker no está corriendo.${NC}"
    echo "Inicia Docker Desktop y vuelve a intentar."
    exit 1
fi

# Verificar que el contenedor existe
if ! docker ps --format '{{.Names}}' | grep -q "$CONTAINER"; then
    # Intentar con nombre alternativo
    CONTAINER=$(docker-compose ps -q web 2>/dev/null || true)
    if [ -z "$CONTAINER" ]; then
        echo -e "${RED}Error: No se encontró el contenedor de Odoo.${NC}"
        echo "Ejecuta 'docker-compose up -d' primero."
        exit 1
    fi
fi

# Definir módulos según argumento
if [ -z "$1" ]; then
    MODULES="ferreteria_inventario,ferreteria_ventas,ferreteria_compras,ferreteria_facturacion,ferreteria_finanzas,ferreteria_usuarios"
    echo -e "\n${GREEN}Ejecutando tests de TODOS los módulos...${NC}\n"
else
    case "$1" in
        inventario)  MODULES="ferreteria_inventario" ;;
        ventas)      MODULES="ferreteria_ventas" ;;
        compras)     MODULES="ferreteria_compras" ;;
        facturacion) MODULES="ferreteria_facturacion" ;;
        finanzas)    MODULES="ferreteria_finanzas" ;;
        usuarios)    MODULES="ferreteria_usuarios" ;;
        *)
            echo -e "${RED}Módulo no reconocido: $1${NC}"
            echo "Opciones: inventario, ventas, compras, facturacion, finanzas, usuarios"
            exit 1
            ;;
    esac
    echo -e "\n${GREEN}Ejecutando tests de: ${MODULES}...${NC}\n"
fi

# Eliminar base de datos de test anterior si existe
echo -e "${YELLOW}Preparando base de datos de test...${NC}"
docker exec "$CONTAINER" psql -U odoo -h db -c "DROP DATABASE IF EXISTS ${DB_TEST};" postgres 2>/dev/null || true

# Ejecutar tests
echo -e "${YELLOW}Ejecutando tests (esto puede tomar unos minutos)...${NC}\n"

docker exec "$CONTAINER" odoo \
    --test-enable \
    --stop-after-init \
    -d "$DB_TEST" \
    -i "$MODULES" \
    --log-level=test 2>&1 | tee /tmp/odoo_test_output.log

# Verificar resultado
if grep -q "FAIL" /tmp/odoo_test_output.log; then
    echo -e "\n${RED}=============================================${NC}"
    echo -e "${RED}  ALGUNOS TESTS FALLARON${NC}"
    echo -e "${RED}=============================================${NC}"
    echo -e "Revisa el log completo arriba para ver los detalles.\n"
    exit 1
elif grep -q "ERROR" /tmp/odoo_test_output.log; then
    echo -e "\n${RED}=============================================${NC}"
    echo -e "${RED}  ERRORES DURANTE LA EJECUCIÓN${NC}"
    echo -e "${RED}=============================================${NC}"
    echo -e "Revisa el log completo arriba para ver los detalles.\n"
    exit 1
else
    echo -e "\n${GREEN}=============================================${NC}"
    echo -e "${GREEN}  TODOS LOS TESTS PASARON CORRECTAMENTE${NC}"
    echo -e "${GREEN}=============================================${NC}\n"
fi

# Limpiar base de datos de test
echo -e "${YELLOW}Limpiando base de datos de test...${NC}"
docker exec "$CONTAINER" psql -U odoo -h db -c "DROP DATABASE IF EXISTS ${DB_TEST};" postgres 2>/dev/null || true

echo -e "${GREEN}¡Listo!${NC}"
