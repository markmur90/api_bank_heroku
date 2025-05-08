#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$HOME/Documentos/GitHub/api_bank_h2"
VENV_PATH="$HOME/Documentos/Entorno/venvAPI"
INTERFAZ="wlan0"

confirmar() {
    echo ""
    echo ""
    printf "\033[1;34m🔷 ¿Confirmas la ejecución de: «%s»? (s/n):\033[0m " "$1"
    read -r resp
    [[ "$resp" == "s" || -z "$resp" ]]
}

clear

for PUERTO in 2222 8000 5000 8001 35729; do
    if lsof -i tcp:"$PUERTO" &>/dev/null; then
        if confirmar "Cerrar procesos en puerto $PUERTO"; then
            sudo fuser -k "${PUERTO}"/tcp || true
            echo -e "\033[1;32m✅ Puerto $PUERTO liberado con éxito.\033[0m"
        fi
    fi
done

if confirmar "Detener contenedores Docker activos"; then
    ACTIVE_CONTAINERS=$(docker ps -q)
    if [ -n "$ACTIVE_CONTAINERS" ]; then
        sudo docker stop $ACTIVE_CONTAINERS
        echo -e "\033[1;32m🛑 Todos los contenedores Docker activos han sido detenidos.\033[0m"
    else
        echo -e "\033[1;33mℹ️ No se detectan contenedores Docker en ejecución.\033[0m"
    fi
fi

if confirmar "Eliminar contenedores Docker"; then
    ALL_CONTAINERS=$(docker ps -aq)
    if [ -n "$ALL_CONTAINERS" ]; then
        sudo docker rm $ALL_CONTAINERS
        echo -e "\033[1;32m🗑️ Todos los contenedores Docker han sido eliminados.\033[0m"
    else
        echo -e "\033[1;33mℹ️ No hay contenedores Docker para eliminar.\033[0m"
    fi
fi

if confirmar "Eliminar imágenes Docker"; then
    ALL_IMAGES=$(docker images -q)
    if [ -n "$ALL_IMAGES" ]; then
        sudo docker rmi $ALL_IMAGES
        echo -e "\033[1;32m🗑️ Todas las imágenes Docker han sido eliminadas.\033[0m"
    else
        echo -e "\033[1;33mℹ️ No se encontraron imágenes Docker para eliminar.\033[0m"
    fi
fi

if confirmar "Actualizar el sistema"; then
    sudo apt-get update && sudo apt-get full-upgrade -y
    sudo apt-get autoremove -y && sudo apt-get clean
    echo -e "\033[1;32m🎉 Sistema actualizado correctamente.\033[0m"
fi

if confirmar "Configurar entorno Python y PostgreSQL"; then
    export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
    echo -e "\033[1;32m🐍 Entorno virtual y PostgreSQL configurados y en ejecución.\033[0m"
fi

if confirmar "Configurar UFW"; then
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 2222/tcp
    sudo ufw allow 8000/tcp
    sudo ufw allow 5000/tcp
    sudo ufw allow 35729/tcp
    sudo ufw allow from 127.0.0.1 to any port 8001 proto tcp comment "Gunicorn local backend"
    sudo ufw deny 22/tcp comment "Bloquear SSH real en 22"
    sudo ufw enable
    echo -e "\033[1;32m🔐 Reglas de UFW aplicadas con éxito.\033[0m"
fi

if confirmar "Cambiar MAC de la interfaz $INTERFAZ"; then
    sudo ip link set "$INTERFAZ" down
    MAC_ANTERIOR=$(sudo macchanger -s "$INTERFAZ" | awk '/Current MAC:/ {print $3}')
    MAC_NUEVA=$(sudo macchanger -r "$INTERFAZ" | awk '/New MAC:/ {print $3}')
    sudo ip link set "$INTERFAZ" up
    echo -e "\033[1;32m🔍 MAC anterior: $MAC_ANTERIOR\033[0m"
    echo -e "\033[1;32m🎉 MAC asignada:    $MAC_NUEVA\033[0m"
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
    GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_USER};
    GRANT CREATE ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF
    echo "🗄️ La base de datos «${DB_NAME}» ya existe. Procediendo a eliminarla..."
fi

if confirmar "Ejecutar migraciones y cargar datos"; then
    source "$VENV_PATH/bin/activate"
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
    echo ""
    echo "🔄 Generando migraciones de Django..."
    python manage.py makemigrations
    echo ""
    echo "⏳ Aplicando migraciones de la base de datos..."
    python manage.py migrate
    echo ""
    echo "📥 Cargando fixtures desde bdd.json..."
    python manage.py loaddata bdd.json
    echo ""
    echo -e "\033[1;32m✅ Migraciones aplicadas y datos cargados correctamente.\033[0m"
elif confirmar "Crear superusuario de Django"; then
    source "$VENV_PATH/bin/activate"
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
    echo ""
    echo "🔄 Generando migraciones de Django..."
    python manage.py makemigrations
    echo ""
    echo "⏳ Aplicando migraciones de la base de datos..."
    python manage.py migrate
    echo ""
    echo "👤 Creando superusuario de Django..."
    python manage.py createsuperuser
    echo ""
    echo -e "\033[1;32m👤 Superusuario de Django creado con éxito.\033[0m"
fi

if confirmar "Copiar proyecto y crear respaldo ZIP"; then
    SOURCE="$PROJECT_ROOT/"
    DEST="$HOME/Documentos/GitHub/api_bank_heroku/"
    BACKUP_DIR="$HOME/Documentos/GitHub/backup/"
    read -p "Campo adicional para el nombre del ZIP (opcional): " SUFFIX
    TIMESTAMP=$(date +%Y%m%d__%H-%M-%S)
    BACKUP_ZIP="${BACKUP_DIR}${TIMESTAMP}_backup_api_bank_h2${SUFFIX}.zip"
    sudo mkdir -p "$DEST" "$BACKUP_DIR"
    echo "📦 Creando archivo ZIP de respaldo..."
    (
        cd "$(dirname "$SOURCE")"
        sudo zip -r "$BACKUP_ZIP" "$(basename "$SOURCE")" --exclude="*.sqlite3" --exclude="*.db" --exclude="*.pyc" --exclude="*.pyo"
    )
    echo ""
    echo "🔄 Sincronizando archivos al destino..."
    rsync -av --exclude=".gitattributes" --exclude="auto_commit" --exclude="*.db" --exclude="*.sqlite3" --exclude="temp/" "$SOURCE" "$DEST"
    echo ""
    echo -e "\033[1;32m✅ Respaldo ZIP creado en: $BACKUP_ZIP\033[0m"
    cd "$BACKUP_DIR" || exit 1
    TODAY=$(date +%Y%m%d)
    today_files=( $(ls -1t "${TODAY}__"*.zip 2>/dev/null) )
    for f in "${today_files[@]:10}"; do sudo rm -- "$f"; done
    dates=( $(ls -1 *.zip | grep -E '^[0-9]{8}__' | cut -c1-8 | grep -v "^$TODAY" | sort -u) )
    for d in "${dates[@]}"; do
        files=( $(ls -1t "${d}__"*.zip) )
        for f in "${files[@]:1}"; do sudo rm -- "$f"; done
    done
    echo ""
    echo "🧹 Archivos ZIP antiguos eliminados."
fi

if confirmar "Sincronizar base de datos remota"; then
    LOCAL_DB_NAME="mydatabase"
    LOCAL_DB_USER="markmur88"
    LOCAL_DB_HOST="localhost"
    REMOTE_DB_URL="postgres://usuario:contraseña@servidor:5432/d9vb99r9t1m7kt"

    # 🕒 Marca de tiempo para el backup
    DATE=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="$HOME/Documentos/GitHub/backup/"
    BACKUP_FILE="${BACKUP_DIR}backup_${DATE}.sql"
    if ! command -v pv > /dev/null 2>&1; then
        echo "⚠️ La herramienta 'pv' no está instalada. Instálala con: sudo apt install pv"
        exit 1
    fi
    echo ""
    echo "🗄️ Iniciando reinicio de la base de datos remota..."
    psql "$REMOTE_DB_URL" -q -c "DROP SCHEMA public CASCADE;..." || { echo "❌ Ocurrió un error al reiniciar la base de datos remota. Abortando operación."; exit 1; }
    echo ""
    echo "💾 Generando respaldo local de la base de datos..."
    pg_dump --no-owner --no-acl -U "$LOCAL_DB_USER" -h "$LOCAL_DB_HOST" "$LOCAL_DB_NAME" > "$BACKUP_FILE" || { echo "❌ Error al generar el respaldo local. Abortando operación."; exit 1; }
    echo ""
    echo "🌐 Importando respaldo en la base de datos remota..."
    pv "$BACKUP_FILE" | psql "$REMOTE_DB_URL" -q > /dev/null || { echo "❌ Error al importar el respaldo remoto. Abortando operación."; exit 1; }
    echo ""
    echo "🎉 Sincronización completada: respaldo guardado en $BACKUP_FILE"
    echo ""
    echo "🧹 Archivos SQL antiguos eliminados."
fi

if confirmar "Recolectar estáticos y desplegar"; then
    source "$VENV_PATH/bin/activate"
    python manage.py collectstatic --noinput
    export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"
    nohup gunicorn config.wsgi:application \
        --workers 3 \
        --bind 0.0.0.0:8001 \
        --keep-alive 2 \
        > gunicorn.log 2>&1 < /dev/null &
    nohup python honeypot.py \
        > honeypot.log 2>&1 < /dev/null &
    nohup livereload --host 0.0.0.0 --port 35729 static/ -t templates/ \
        > livereload.log 2>&1 < /dev/null &
    sleep 5
    firefox --new-tab http://0.0.0.0:8000 --new-tab http://localhost:5000
    echo -e "\033[1;32m🚧 Gunicorn, honeypot y livereload están activos. Presiona Ctrl+C para detenerlos.\033[0m"
    wait
fi

echo -e "\033[1;35m\n🏁 Todos los procesos han finalizado correctamente.\033[0m"
