#!/usr/bin/env bash
set -euo pipefail

PROMPT_MODE=true
SYNC_REMOTE_DB=true
GUNICORN=true

function usage() {
    echo -e "\033[7;30mUso: $0 [-a|--all] [-s|--step] [-o|--omit-remote-sync] [-g|--omit-gunicorn] [-h|--help]"
}
while [[ $# -gt 0 ]]; do
    case "$1" in
        -a|--all) PROMPT_MODE=false; shift ;;
        -s|--step) PROMPT_MODE=true; shift ;;
        -o|--omit-remote-sync) SYNC_REMOTE_DB=false; shift ;;
        -g|--omit-gunicorn) GUNICORN=false; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo -e "\033[7;30mOpción desconocida: $1\033[0m"; usage; exit 1 ;;
    esac
done

confirmar() {
    [[ "$PROMPT_MODE" == false ]] && return 0
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
    printf "\033[1;34m🔷 ¿Confirmas: %s? (s/n):\033[0m " "$1"
    read -r resp
    [[ "$resp" == "s" || -z "$resp" ]]
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
}


PROJECT_ROOT="$HOME/Documentos/GitHub/api_bank_h2"
BACKUP_DIR="$HOME/Documentos/GitHub/backup/"
HEROKU_ROOT="$HOME/Documentos/GitHub/api_bank_heroku"
VENV_PATH="$HOME/Documentos/Entorno/venvAPI"
INTERFAZ="wlan0"


mkdir -p "$BACKUP_DIR"

# 1. Puertos
for PUERTO in 2222 8000 5000 8001 35729; do
    if lsof -i tcp:"$PUERTO" &>/dev/null; then
        if confirmar "Cerrar procesos en puerto $PUERTO"; then
            sudo fuser -k "${PUERTO}"/tcp || true
            echo -e "\033[7;30m✅ Puerto $PUERTO liberado.\033[0m"
        fi
    fi
done

# 2. Docker
if confirmar "Detener contenedores Docker"; then
    PIDS=$(docker ps -q)
    if [ -n "$PIDS" ]; then
        docker stop $PIDS
        echo -e "\033[7;30m🐳 Contenedores detenidos.\033[0m"
    else
        echo -e "\033[7;30m🐳 No hay contenedores.\033[0m"
    fi
fi

if confirmar "Configurar venv y PostgreSQL"; then
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip
    pip install -r "$PROJECT_ROOT/requirements.txt"
    sudo apt install -y postgresql postgresql-contrib
    echo -e "\033[7;30m🐍 Entorno y PostgreSQL listos.\033[0m"
fi

# 3. Actualizar sistema
if confirmar "Actualizar sistema"; then
    echo -e "\033[7;30m Actualizando... \033[0m"
    sudo apt update && sudo apt upgrade -y
    echo -e "\033[7;30m🔄 Sistema actualizado.\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
fi

# 4. Entorno Python y PostgreSQL
if confirmar "Configurar venv y PostgreSQL"; then
    echo -e "\033[7;30m Configurando... \033[0m"
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    pip install --upgrade pip
    echo -e "\033[7;30m📦 Instalando dependencias...\033[0m"
    pip install -r "$PROJECT_ROOT/requirements.txt"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
    echo -e "\033[7;30m🐍 Entorno y PostgreSQL listos.\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
fi

# 5. Firewall
if confirmar "Configurar UFW"; then
    echo -e "\033[7;30m Configurando... \033[0m"
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
    echo -e "\033[7;30m🔐 Reglas de UFW aplicadas con éxito.\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
fi

# 6. Cambiar MAC
if confirmar "Cambiar MAC de $INTERFAZ"; then
    echo -e "\033[7;30m Cambiando MAC... \033[0m"
    sudo ip link set "$INTERFAZ" down
    MAC_ANTERIOR=$(sudo macchanger -s "$INTERFAZ" | awk '/Current MAC:/ {print $3}')
    MAC_NUEVA=$(sudo macchanger -r "$INTERFAZ" | awk '/New MAC:/ {print $3}')
    sudo ip link set "$INTERFAZ" up
    echo -e "\033[7;30m🔍 MAC anterior: $MAC_ANTERIOR\033[0m"
    echo -e "\033[7;30m🎉 MAC asignada: $MAC_NUEVA\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
fi

# 7. DB: reset y usuario
if confirmar "Configurar PostgreSQL"; then
    echo -e "\033[7;30m Reseteando... \033[0m"
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
    echo -e "\033[7;30mLa base de datos ${DB_NAME} existe. Eliminándola...\033[0m"
    echo -e "\033[7;30m----\033[0m"
    sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}';"
    sudo -u postgres psql -c "DROP DATABASE ${DB_NAME};"
    echo -e "\033[7;30m----\033[0m"
fi


# Crear la base de datos y asignar permisos
sudo -u postgres psql <<-EOF
CREATE DATABASE ${DB_NAME};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
GRANT CONNECT ON DATABASE ${DB_NAME} TO ${DB_USER};
GRANT CREATE ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF
    echo -e "\033[7;30mBase de datos y usuario recreados.\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
fi

if confirmar "Ejecutar migraciones y cargar datos"; then
    echo -e "\033[7;30m Ejecutando migraciones y carga... \033[0m"
    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m🔄 Generando migraciones de Django... \033[0m"
    python manage.py makemigrations
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m⏳ Aplicando migraciones de la base de datos... \033[0m"
    python manage.py migrate
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m📥 Cargando fixtures desde bdd.json...\033[0m"
    LOADDATA_OUT=$(python manage.py loaddata bdd.json)
    echo -e "\033[7;30m📥 Datos subidos:\033[0m"
    echo -e "\033[7;30m$LOADDATA_OUT\033[0m"
    if echo -e "\033[7;30m$LOADDATA_OUT\033[0m" | grep -q 'Installed 0'; then
        if confirmar "Crear superusuario de Django"; then
            python manage.py createsuperuser
            echo -e "\033[7;30m👤 Superusuario creado.\033[0m"
            echo -e "\033[7;30m----\033[0m"
            echo -e "\033[7;30m----\033[0m"
        fi
    else
        echo -e "\033[7;30m👥 Datos cargados, se omite superusuario.\033[0m"
        echo -e "\033[7;30m----\033[0m"
        echo -e "\033[7;30m----\033[0m"
    fi
fi

if confirmar "Copiar proyecto y crear respaldo ZIP"; then
    SOURCE="$PROJECT_ROOT/"
    DEST="$HOME/Documentos/GitHub/api_bank_heroku/"
    BACKUP_DIR="$HOME/Documentos/GitHub/backup/"
    read -p "Campo adicional para el nombre del ZIP (opcional): " SUFFIX
    TIMESTAMP=$(date +%Y%m%d__%H-%M-%S)
    BACKUP_ZIP="${BACKUP_DIR}${TIMESTAMP}_backup_api_bank_h2${SUFFIX}.zip"
    sudo mkdir -p "$DEST" "$BACKUP_DIR"
    (
        cd "$(dirname "$SOURCE")"
        sudo zip -r "$BACKUP_ZIP" "$(basename "$SOURCE")" --exclude=".git/" --exclude="*.zip" --exclude="__pycache__/" --exclude="*.sqlite3" --exclude="*.db" --exclude="*.pyc" --exclude="*.pyo"
    )
    echo ""
    rsync -av --exclude=".gitattributes" --exclude="auto_commit_sync.sh" --exclude="manage.py" --exclude="*local.py" --exclude=".git/" --exclude="gunicorn.log" --exclude="honeypot_logs.csv" --exclude="token.md" --exclude="url_help.md" --exclude="honeypot.py" --exclude="URL_TOKEN.md" --exclude="01_full.sh" --exclude="05Gunicorn.sh" --exclude="*.zip" --exclude="*.db" --exclude="*.sqlite3" --exclude="temp/" "$SOURCE" "$DEST"
    echo ""
    echo -e "\033[1;32mCopia y respaldo ZIP creados: $BACKUP_ZIP\033[0m"
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
    echo "🗑️ Limpieza de archivos zip completada."
fi



if [[ "$SYNC_REMOTE_DB" == true ]] || confirmar "Sincronizar base de datos Heroku"; then
    echo -e "\033[7;30m🚀 Sincronizando base de datos remota... \033[0m"
    LOCAL_DB_NAME="mydatabase"
    LOCAL_DB_USER="markmur88"
    LOCAL_DB_HOST="localhost"
    REMOTE_DB_URL="postgres://ue2erdhkle4v0h:pa1773a2b68d739e66a794acd529d1b60c016733f35be6884a9f541365d5922cf@ec2-63-33-30-239.eu-west-1.compute.amazonaws.com:5432/d9vb99r9t1m7kt"
    # **🕒 Marca de tiempo para el backup**
    DATE=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="$HOME/Documentos/GitHub/backup/"
    # Crear el directorio de backup si no existe
    BACKUP_FILE="${BACKUP_DIR}backup_${DATE}.sql"
    if ! command -v pv > /dev/null 2>&1; then
        echo -e "\033[7;30m⚠️ La herramienta 'pv' no está instalada. Instálala con: sudo apt install pv \033[0m"
    fi
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m🧹 Reseteando base de datos remota... \033[0m"
    psql "$REMOTE_DB_URL" -q -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || { echo -e "\033[7;30m❌ Error al resetear la DB remota. Abortando.\033[0m"; exit 1; }
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m📦 Generando backup local... \033[0m"
    pg_dump --no-owner --no-acl -U "$LOCAL_DB_USER" -h "$LOCAL_DB_HOST" -d "$LOCAL_DB_NAME" > "$BACKUP_FILE" || { echo -e "\033[7;30m❌ Error haciendo el backup local. Abortando.\033[0m"; exit 1; }
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m🌐 Importando backup en la base de datos remota... \033[0m"
    pv "$BACKUP_FILE" | psql "$REMOTE_DB_URL" -q > /dev/null || { echo -e "\033[7;30m❌ Error al importar el backup en la base de datos remota.\033[0m"; exit 1; }
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m✅ Sincronización completada con éxito: "$BACKUP_FILE"\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[1;32mCopia y respaldo ZIP creados: "$BACKUP_FILE"\033[0m"

fi

if [[ "$PROMPT_MODE" == true ]] || confirmar "📦 Deploy en Heroku... \033[0m"; then
    echo -e "\033[7;30m Haciendo deploy... \033[0m"
    cd "$HEROKU_ROOT" || { echo -e "\033[7;30m❌ Error al acceder a "$HEROKU_ROOT"\033[0m"; exit 1; }
    # Git commit y push (automático)
    cd "$HEROKU_ROOT"
    git add --all
    git commit -m "fix: Actualizar ajustes"
    git push origin api-bank || { echo -e "\033[7;30m❌ Error al subir a GitHub\033[0m"; exit 1; }
    # Deploy en Heroku (sin confirmación)
    cd "$HEROKU_ROOT"
    heroku login || { echo -e "\033[7;30m❌ Error en login de Heroku\033[0m"; exit 1; }
    cd "$HEROKU_ROOT"
    git push heroku api-bank:main || { echo -e "\033[7;30m❌ Error en deploy\033[0m"; exit 1; }
    cd "$HEROKU_ROOT"
    cd "$PROJECT_ROOT"
    echo -e "\033[7;30m✅ ¡Deploy completado!\033[0m"
    echo -e "\033[7;30m----\033[0m"
    echo -e "\033[7;30m----\033[0m"
    exit 0
fi

if [[ "$GUNICORN" == true ]] || confirmar "🚀 Iniciar Gunicorn, honeypot y livereload simultáneamente... \033[0m"; then
    echo -e "\033[7;30m🚀 Iniciar Gunicorn, honeypot y livereload simultáneamente...\033[0m"
    # clear
    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"
    python manage.py collectstatic --noinput
    export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"
    # Función para limpiar y salir
    cleanup() {
        echo -e "\n\033[1;33mDeteniendo todos los servicios...\033[0m"
        # Matar todos los procesos en segundo plano
        pids=$(jobs -p)
        if [ -n "$pids" ]; then
            kill $pids 2>/dev/null
        fi
        # Liberar puertos
        for port in 8001 5000 35729; do
            if lsof -i :$port > /dev/null; then
                echo -e "\033[7;30mLiberando puerto $port...\033[0m"
                kill $(lsof -t -i :$port) 2>/dev/null || true
            fi
        done
        echo -e "\033[1;32mTodos los servicios detenidos y puertos liberados.\033[0m"
        exit 0
    }
    # Configurar trap para Ctrl+C
    trap cleanup SIGINT
    # Liberar puertos si es necesario
    for port in 8001 5000 35729; do
        if lsof -i :$port > /dev/null; then
            echo -e "\033[7;30mLiberando puerto $port...\033[0m"
            echo -e "\033[7;30m----\033[0m"
            echo -e "\033[7;30m----\033[0m"
            kill $(lsof -t -i :$port) 2>/dev/null || true
        fi
    done
    # Iniciar servicios
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
    echo -e "\033[7;30m🚧 Gunicorn, honeypot y livereload están activos. Presiona Ctrl+C para detenerlos.\033[0m"
    # Esperar indefinidamente hasta que se presione Ctrl+C
    while true; do
        sleep 1
    done
fi

clear
echo -e "\033[1;30m\n🏁 ¡Todo completado con éxito!\033[0m"