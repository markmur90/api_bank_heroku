#!/bin/bash

# Configura tus credenciales locales y remotas
LOCAL_DB_NAME="mydatabase"
LOCAL_DB_USER="markmur88"
LOCAL_DB_HOST="localhost"

REMOTE_DB_URL="postgres://ue2erdhkle4v0h:pa1773a2b68d739e66a794acd529d1b60c016733f35be6884a9f541365d5922cf@ec2-63-33-30-239.eu-west-1.compute.amazonaws.com:5432/d9vb99r9t1m7kt"

# Marca de tiempo
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backup_$DATE.sql"

echo "📦 Generando backup local..."
pg_dump --no-owner --no-acl -U "$LOCAL_DB_USER" -h "$LOCAL_DB_HOST" -d "$LOCAL_DB_NAME" > "$BACKUP_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Error haciendo el backup local. Abortando."
    exit 1
fi

echo "🌐 Subiendo backup a la base de datos remota..."
psql "$REMOTE_DB_URL" < "$BACKUP_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Error al importar el backup en la base de datos remota."
    exit 1
fi

echo "✅ Sincronización completada con éxito: $BACKUP_FILE"
