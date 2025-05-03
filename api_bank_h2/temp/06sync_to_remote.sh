#!/usr/bin/env bash
set -euo pipefail

# Configura tus credenciales locales y remotas
LOCAL_DB_NAME="mydatabase"
LOCAL_DB_USER="markmur88"
LOCAL_DB_HOST="localhost"
REMOTE_DB_URL="postgres://ue2erdhkle4v0h:pa1773a2b68d739e66a794acd529d1b60c016733f35be6884a9f541365d5922cf@ec2-63-33-30-239.eu-west-1.compute.amazonaws.com:5432/d9vb99r9t1m7kt"

# **🕒 Marca de tiempo para el backup**
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/home/markmur88/Documentos/GitHub/backup/"
# Crear el directorio de backup si no existe
BACKUP_FILE="${BACKUP_DIR}backup_$DATE.sql"
if ! command -v pv > /dev/null 2>&1; then
    echo "pv no está instalado. Instálalo: sudo apt install pv"
    exit 1
fi
echo ""
echo "🧹 Reseteando base de datos remota..."
psql "$REMOTE_DB_URL" -q -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || { echo "❌ Error al resetear la DB remota. Abortando."; exit 1; }
echo ""
echo "📦 Generando backup local..."
pg_dump --no-owner --no-acl -U "$LOCAL_DB_USER" -h "$LOCAL_DB_HOST" -d "$LOCAL_DB_NAME" > "$BACKUP_FILE" || { echo "❌ Error haciendo el backup local. Abortando."; exit 1; }
echo ""
echo "🌐 Importando backup en la base de datos remota..."
pv "$BACKUP_FILE" | psql "$REMOTE_DB_URL" -q > /dev/null || { echo "❌ Error al importar el backup en la base de datos remota."; exit 1; }
echo ""
echo "✅ Sincronización completada con éxito: $BACKUP_FILE"
echo ""

# **🗑️ Limpiar backups viejos**
# Eliminar backups más antiguos de 7 días
find "$BACKUP_DIR" -type f -name "backup_*.sql" -mtime +7 -exec rm {} \; || { echo "❌ Error al limpiar backups viejos."; exit 1; }
echo "🗑️ Limpieza de backups viejos completada."
echo ""
echo "🚀 Script ejecutado con éxito."
echo ""
