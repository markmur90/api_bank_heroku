#!/bin/bash

# filepath: /home/kali/Documentos/Heroku/config/reset_database.sh

# Variables
DB_NAME="mydatabase"
DB_USER="markmur88"

# Ejecutar comandos en PostgreSQL
sudo -u postgres psql <<EOF
DROP DATABASE $DB_NAME;
CREATE DATABASE $DB_NAME;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
GRANT CONNECT ON DATABASE $DB_NAME TO $DB_USER;
GRANT CREATE ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo "Operaciones en la base de datos completadas."