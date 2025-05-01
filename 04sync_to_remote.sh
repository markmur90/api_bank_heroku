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

echo " "

# **🧹 Reseteando base de datos remota**
echo "🧹 **Reseteando base de datos remota...**"
psql "$REMOTE_DB_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" \
  || { echo "❌ **Error al resetear la DB remota. Abortando.**"; exit 1; }

echo " "

# **📦 Generando backup local**
echo "📦 **Generando backup local...**"
pg_dump --no-owner --no-acl -U "$LOCAL_DB_USER" -h "$LOCAL_DB_HOST" -d "$LOCAL_DB_NAME" > "$BACKUP_FILE"
if [ $? -ne 0 ]; then
    echo "❌ **Error haciendo el backup local. Abortando.**"
    exit 1
fi

echo " "

# **🌐 Importando backup en la base de datos remota**
echo "🌐 **Importando backup en la base de datos remota...**"
psql "$REMOTE_DB_URL" < "$BACKUP_FILE"
if [ $? -ne 0 ]; then
    echo "❌ **Error al importar el backup en la base de datos remota.**"
    exit 1
fi

echo " "

echo "✅ **Sincronización completada con éxito: $BACKUP_FILE**"

echo " "
