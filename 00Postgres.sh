#!/bin/bash

# Variables
DB_NAME="mydatabase"
DB_USER="markmur88"
DB_PASSWORD="Ptf8454Jd55"

# Ejecutar comandos en PostgreSQL
sudo -u postgres psql <<-EOF
DO \$\$
BEGIN
    -- Verificar si el usuario ya existe
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
        CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
    END IF;
END
\$\$;

-- Asignar permisos al usuario
ALTER USER ${DB_USER} WITH SUPERUSER;
GRANT USAGE, CREATE ON SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON SCHEMA public TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};

-- Verificar si la base de datos existe antes de eliminarla
DO \$\$
BEGIN
    IF EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}') THEN
        PERFORM pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}';
        DROP DATABASE ${DB_NAME};
    END IF;
END
\$\$;

-- Crear la base de datos y asignar permisos
CREATE DATABASE ${DB_NAME};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_USER};
GRANT CREATE ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF

echo "Operaciones en la base de datos completadas."