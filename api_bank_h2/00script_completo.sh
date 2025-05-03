#!/usr/bin/env bash
set -euo pipefail

source "$HOME/Documentos/Entorno/venvAPI/bin/activate"

INTERFAZ="wlan0"

confirmar(){
    echo ""
    echo -e "\033[1;34m¿Deseas ejecutar: $1? (s/n):\033[0m"
    read -r resp
    [[ "$resp" == "s" ]]
}

if confirmar "Actualización del sistema"; then
    echo -e "\033[1;34m🔄 Actualizando sistema...\033[0m"
    sudo apt-get update && sudo apt-get full-upgrade -y
    sudo apt-get autoremove -y && sudo apt-get clean
    echo -e "\033[32m✅ Sistema actualizado.\033[0m"
fi

if confirmar "Configuración del firewall UFW"; then
    echo -e "\033[1;34m🛡️  Configurando UFW...\033[0m"
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp
    sudo ufw allow 2222/tcp
    sudo ufw allow 5000/tcp
    sudo ufw allow 8000/tcp
    sudo ufw enable
    echo -e "\033[32m✅ UFW configurado.\033[0m"
fi

if confirmar "Cambio de MAC en la interfaz $INTERFAZ"; then
    echo -e "\033[1;34m🔄 Cambiando MAC de $INTERFAZ...\033[0m"
    sudo ip link set "$INTERFAZ" down
    anterior=$(sudo macchanger -s "$INTERFAZ" | awk '/Current MAC:/ {print $3}')
    nueva=$(sudo macchanger -r "$INTERFAZ" | awk '/New MAC:/     {print $3}')
    sudo ip link set "$INTERFAZ" up
    echo "MAC anterior: $anterior"
    echo "MAC nueva:    $nueva"
    echo -e "\033[32m✅ MAC cambiada.\033[0m"
fi

if confirmar "Instalar dependencias y ejecutar honeypot+dashboard"; then
    echo -e "\033[1;34m🐍 Instalando Python3 y Flask...\033[0m"
    sudo apt-get install -y python3 python3-pip
    pip3 install flask
    pip3 install -r /home/markmur88/Documentos/GitHub/api_bank_h2/requirements.txt
    echo -e "\033[1;34m🚨 Iniciando honeypot integrado...\033[0m"
    nohup python3 - <<'PYTHON' > honeypot.log 2>&1 &

import socket
import threading
import csv
import os
import datetime
from flask import Flask, render_template_string

HONEYPOT_IP = "0.0.0.0"
HONEYPOT_PORT = 2222
LOG_FILE = "honeypot_logs.csv"
BANNER = b"SSH-2.0-OpenSSH_7.9p1 Debian-10+deb10u2\r\n"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp","ip","data"])

def handle_client(conn, addr):
    timestamp = datetime.datetime.utcnow().isoformat()
    conn.sendall(BANNER)
    data = conn.recv(1024).strip().decode(errors='ignore')
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, addr[0], data])
    conn.close()

def start_honeypot(ip, port):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((ip, port))
    srv.listen(5)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn,addr), daemon=True).start()

def start_dashboard():
    app = Flask(__name__)
    @app.route("/")
    def index():
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, newline='') as f:
                reader = csv.reader(f)
                next(reader)
                logs = list(reader)
        return render_template_string("""
        <html><head><title>Honeypot Logs</title></head><body>
        <h1>Registros</h1><table border=1>
        <tr><th>Tiempo (UTC)</th><th>IP</th><th>Data</th></tr>
        {% for row in logs %}
          <tr><td>{{row[0]}}</td><td>{{row[1]}}</td><td>{{row[2]}}</td></tr>
        {% endfor %}
        </table></body></html>
        """, logs=logs)
    app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=start_honeypot, args=(HONEYPOT_IP,HONEYPOT_PORT), daemon=True).start()
    start_dashboard()

PYTHON
    echo -e "\033[32m✅ Honeypot + dashboard en marcha.\033[0m"
fi

DB_NAME="mydatabase"
DB_USER="markmur88"
DB_PASS="Ptf8454Jd55"

if confirmar "Configuración de PostgreSQL"; then
    echo -e "\033[1;34m🐘 Configurando PostgreSQL...\033[0m"
    sudo -u postgres psql <<EOF
DO \$\$
BEGIN
    -- Verificar si el usuario ya existe
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
        CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
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
    echo -e "\033[32m✅ PostgreSQL listo.\033[0m"
    export DATABASE_URL="postgres://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}"
fi

if confirmar "Volcado de datos (dumpdata)"; then
    echo -e "\033[1;34m📦 Ejecutando dumpdata...\033[0m"
    python3 manage.py makemigrations && python3 manage.py migrate
    python3 manage.py dumpdata --indent 4 > bdd.json
    echo -e "\033[32m✅ bdd.json generado.\033[0m"
fi

if confirmar "Carga de datos (loaddata)"; then
    echo -e "\033[1;34m📥 Ejecutando loaddata...\033[0m"
    python3 manage.py loaddata bdd.json
    echo -e "\033[32m✅ Datos cargados.\033[0m"
fi

if confirmar "Creación de superusuario"; then
    echo -e "\033[1;34m👤 Creando superusuario...\033[0m"
    python3 manage.py createsuperuser
    echo -e "\033[32m✅ Superusuario creado.\033[0m"
fi

SOURCE="/home/markmur88/Documentos/GitHub/api_bank_h2/"
DEST="/home/markmur88/Documentos/GitHub/api_bank_heroku/"
BACKUP_DIR="/home/markmur88/Documentos/GitHub/backup/"
BACKUP_ZIP="${BACKUP_DIR}$(date +%Y%m%d__%H-%M-%S)_backup_api_bank_h2.zip"

if confirmar "Copia del proyecto y respaldo"; then
    echo -e "\033[1;34m💾 Copiando y respaldando proyecto...\033[0m"
    cp -r "${SOURCE}" "${DEST}"
    mkdir -p "${BACKUP_DIR}"
    zip -r "${BACKUP_ZIP}" "${SOURCE}"
    echo -e "\033[32m✅ Copia en ${DEST} y respaldo en ${BACKUP_ZIP}.\033[0m"
fi

LOCAL_DB_NAME="$DB_NAME"
LOCAL_DB_USER="$DB_USER"
LOCAL_DB_HOST="localhost"
REMOTE_DB_URL="postgres://ue2erdhkle4v0h:pa1773a2b68d739e66a794a8c7b4036eaa7972dfbaabc8dfdb23-33-30-239.eu-west-1.compute.amazonaws.com:5432/d9vb99r9t1m7kt"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}backup_${DATE}.sql"

if confirmar "Sincronización con base de datos remota"; then
    echo -e "\033[1;34m🌐 Sincronizando con base de datos remota...\033[0m"
    if ! command -v pv > /dev/null 2>&1; then
        echo -e "\033[1;31mpv no está instalado. Instálalo: sudo apt install pv\033[0m"
        exit 1
    fi
    mkdir -p "${BACKUP_DIR}"
    PGPASSWORD="${DB_PASS}" pg_dump -U "${LOCAL_DB_USER}" -h "${LOCAL_DB_HOST}" "${LOCAL_DB_NAME}" > "${BACKUP_FILE}"
    echo ""
    echo -e "\033[1;34m🌐 Importando backup en la base de datos remota...\033[0m"
    pv "${BACKUP_FILE}" | psql "${REMOTE_DB_URL}" -q > /dev/null || { echo -e "\033[1;31m❌ Error al importar el backup en la base de datos remota.\033[0m"; exit 1; }
    echo ""
    echo -e "\033[32m✅ Sincronización completada con éxito: ${BACKUP_FILE}\033[0m"
    echo ""
    echo -e "\033[1;34m🗑️ Limpiando backups viejos...\033[0m"
    find "${BACKUP_DIR}" -type f -name "backup_*.sql" -mtime +7 -exec rm {} \; || { echo -e "\033[1;31m❌ Error al limpiar backups viejos.\033[0m"; exit 1; }
    echo -e "\033[32m🗑️ Limpieza de backups viejos completada.\033[0m"
    echo ""
fi

if confirmar "Puesta en marcha de Gunicorn y apertura en Mozilla"; then
    echo -e "\033[1;34m🚀 Iniciando Gunicorn...\033[0m"
    python3 manage.py collectstatic --noinput
    nohup gunicorn config.wsgi:application --bind 0.0.0.0:8000 > gunicorn.log 2>&1 &
    echo -e "\033[1;34m🌐 Abriendo Mozilla...\033[0m"
    mozilla --new-tab http://localhost:5000 --new-tab http://localhost:8000 &
    echo -e "\033[32m✅ Gunicorn y navegador listos.\033[0m"
fi