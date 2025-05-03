#!/usr/bin/env bash
set -euo pipefail
#
confirmar() {
    echo ""
    printf "\033[1;34m¿Deseas ejecutar: %s? (s/n):\033[0m " "$1"
    read -r resp
    [[ "$resp" == "s" || -z "$resp" ]]
}

INTERFAZ="wlan0"

clear

for PUERTO in 2222 8000 5000; do
    if lsof -i tcp:"$PUERTO" &>/dev/null; then
        if confirmar "Cerrar procesos en puerto $PUERTO"; then
            sudo fuser -k "${PUERTO}"/tcp || true
            echo -e "\033[1;32mPuerto $PUERTO liberado.\033[0m"
        fi
    fi
done

if confirmar "Detener contenedores Docker activos"; then
    PIDS=$(docker ps -q)
    if [ -n "$PIDS" ]; then
        sudo docker stop $PIDS
        echo -e "\033[1;32mContenedores Docker activos detenidos.\033[0m"
    else
        echo -e "\033[1;33mNo hay contenedores Docker activos.\033[0m"
    fi

    ALL_CONTAINERS=$(docker ps -a -q)
    if [ -n "$ALL_CONTAINERS" ]; then
        sudo docker rm $ALL_CONTAINERS
        echo -e "\033[1;32mTodos los contenedores eliminados.\033[0m"
    else
        echo -e "\033[1;33mNo hay contenedores para eliminar.\033[0m"
    fi

    ALL_IMAGES=$(docker images -q)
    if [ -n "$ALL_IMAGES" ]; then
        sudo docker rmi $ALL_IMAGES
        echo -e "\033[1;32mTodas las imágenes Docker eliminadas.\033[0m"
    else
        echo -e "\033[1;33mNo hay imágenes Docker para eliminar.\033[0m"
    fi
fi


if confirmar "Actualizar el sistema"; then
    sudo apt-get update && sudo apt-get full-upgrade -y
    sudo apt-get autoremove -y && sudo apt-get clean
    echo -e "\033[1;32mSistema actualizado.\033[0m"
fi

if confirmar "Configurar entorno Python y PostgreSQL"; then
    export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"
    python3 -m venv "$HOME/Documentos/Entorno/venvAPI"
    source "$HOME/Documentos/Entorno/venvAPI/bin/activate"
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
    echo -e "\033[1;32mEntorno y PostgreSQL listos.\033[0m"
fi

if confirmar "Configurar UFW"; then
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp
    sudo ufw allow 2222/tcp
    sudo ufw allow 8000/tcp
    sudo ufw allow 5000/tcp
    sudo ufw enable
    echo -e "\033[1;32mReglas de UFW aplicadas.\033[0m"
fi

if confirmar "Cambiar MAC de la interfaz $INTERFAZ"; then
    sudo ip link set "$INTERFAZ" down
    MAC_ANTERIOR=$(sudo macchanger -s "$INTERFAZ" | awk '/Current MAC:/ {print $3}')
    MAC_NUEVA=$(sudo macchanger -r "$INTERFAZ" | awk '/New MAC:/ {print $3}')
    sudo ip link set "$INTERFAZ" up
    echo -e "\033[1;32mMAC anterior: $MAC_ANTERIOR\033[0m"
    echo -e "\033[1;32mMAC nueva:    $MAC_NUEVA\033[0m"
fi

if confirmar "Resetear base de datos y crear usuario en PostgreSQL"; then
    DB_NAME="mydatabase"
    DB_USER="markmur88"
    DB_PASSWORD="Ptf8454Jd55"
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
EOF

# Verificar si la base de datos existe y eliminarla si es necesario
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1
if [ $? -eq 0 ]; then
    echo "La base de datos ${DB_NAME} existe. Eliminándola..."
    sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}';"
    sudo -u postgres psql -c "DROP DATABASE ${DB_NAME};"
fi

# Crear la base de datos y asignar permisos
sudo -u postgres psql <<-EOF
CREATE DATABASE ${DB_NAME};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_USER};
GRANT CREATE ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF
    echo -e "\033[1;32mBase de datos y usuario recreados.\033[0m"
fi

if confirmar "Ejecutar migraciones y cargar datos"; then
    pip3 install -r requirements.txt
    python3 manage.py makemigrations
    python3 manage.py migrate
    python3 manage.py loaddata bdd.json
    echo -e "\033[1;32mMigraciones y datos cargados.\033[0m"
else
    if confirmar "Crear superusuario de Django"; then
        pip3 install -r requirements.txt
        python3 manage.py makemigrations
        python3 manage.py migrate
        python3 manage.py createsuperuser
        echo -e "\033[1;32mSuperusuario creado.\033[0m"
    fi
fi

if confirmar "Copiar proyecto y crear respaldo ZIP"; then
    SOURCE="/home/markmur88/Documentos/GitHub/api_bank_h2/"
    DEST="/home/markmur88/Documentos/GitHub/api_bank_heroku/"
    BACKUP_DIR="/home/markmur88/Documentos/GitHub/backup/"
    read -p "Campo adicional para el nombre del ZIP (opcional): " SUFFIX
    TIMESTAMP=$(date +%Y%m%d__%H-%M-%S)
    BACKUP_ZIP="${BACKUP_DIR}${TIMESTAMP}_backup_api_bank_h2${SUFFIX}.zip"
    sudo mkdir -p "$DEST" "$BACKUP_DIR"
    sudo cp -r "$SOURCE" "$DEST"
    sudo zip -r "$BACKUP_ZIP" "$SOURCE"
    echo -e "\033[1;32mCopia y respaldo ZIP creados: $BACKUP_ZIP\033[0m"
fi

if confirmar "Sincronizar base de datos remota"; then
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
fi

if confirmar "Abrir Firefox para la aplicación Django"; then
    firefox --new-tab http://0.0.0.0:8000 &
fi

if confirmar "Abrir Firefox para el dashboard del honeypot"; then
    firefox --new-tab http://127.0.0.1:5000 &
fi

if confirmar "Iniciar Gunicorn y honeypot simultáneamente"; then
    python3 manage.py collectstatic --noinput
    export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"
    nohup gunicorn config.wsgi:application --bind 0.0.0.0:8000 > gunicorn.log 2>&1 &
    sudo ./deploy_honeypot.sh
    echo -e "\033[1;32mGunicorn y honeypot en marcha.\033[0m"
fi

echo -e "\033[1;35m\n¡Todos los procesos han terminado!\033[0m"
