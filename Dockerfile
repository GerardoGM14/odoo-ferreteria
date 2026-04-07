FROM odoo:17.0

USER root

# Dependencias Python adicionales requeridas por los módulos custom
RUN pip install --no-cache-dir \
    openpyxl

USER odoo
