#!/usr/bin/env bash
set -euo pipefail

confirmar() {
    echo ""
    printf "\033[1;34m¿Deseas ejecutar: %s? (s/n):\033[0m " "$1"
    read -r resp
    [[ "$resp" == "s" || -z "$resp" ]]
}

INTERFAZ="wlan0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HONEYPOT_DIR="$SCRIPT_DIR/honeypot"

clear

for PUERTO in 2222 8000 5000; do
    if lsof -i tcp:"$PUERTO" &>/dev/null; then
        if confirmar "Cerrar procesos en puerto $PUERTO"; then
            sudo fuser -k "${PUERTO}"/tcp || true
            echo -e "\033[1;32mPuerto $PUERTO liberado.\033[0m"
        fi
    fi
done

echo "[+] Habilitando IP forwarding"
sudo sysctl -w net.ipv4.ip_forward=1

echo "[+] Configurando iptables para redirección en la interfaz $INTERFAZ"
sudo iptables -t nat -A PREROUTING -i "$INTERFAZ" -p tcp --dport 2222 -j REDIRECT --to-port 2222
sudo iptables -t nat -A PREROUTING -i "$INTERFAZ" -p tcp --dport 8000 -j REDIRECT --to-port 8000
sudo iptables -t nat -A PREROUTING -i "$INTERFAZ" -p tcp --dport 5000 -j REDIRECT --to-port 5000

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
    echo -e "\033[1;32mGunicorn y honeypot en marcha.\033[0m"
fi


echo "[+] Instalando dependencias del sistema..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg python3 python3-pip

echo "[+] Configurando firewall UFW..."
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 5000/tcp

echo "[+] Configurando repositorio Docker para Debian bullseye..."
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bullseye stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo systemctl enable docker
sudo systemctl start docker

echo "[+] Añadiendo usuario al grupo docker..."
USER_TO_ADD=${SUDO_USER:-$USER}
sudo usermod -aG docker "$USER_TO_ADD"

echo "[+] Preparando estructura del honeypot..."
mkdir -p "$HONEYPOT_DIR"/{cfg,data/json,web/templates}

echo "[+] Generando configuración de Cowrie..."
cat << 'EOF' > "$HONEYPOT_DIR"/cfg/cowrie.cfg
[ssh]
listen_addr = 0.0.0.0
listen_port = 2222

[output_json]
enabled = true
path = /cowrie/data/json

[userdb]
authorized = admin:5f4dcc3b5aa765d61d8327deb882cf99,guest:084e0343a0486ff05530df6c705c8bb4

[commands]
enabled = true
extensions = ls,cat,uname,whoami,pwd,ps,ifconfig

[honeypot]
id = honeypot-vulntrap
loglevel = INFO
EOF

echo "[+] Generando visor web Flask..."
mkdir -p "$HONEYPOT_DIR"/web
cat << 'EOF' > "$HONEYPOT_DIR"/web/app.py
from flask import Flask, render_template, jsonify
from pathlib import Path
import json

app = Flask(__name__)
LOGFILE = Path("/cowrie/data/json/cowrie.json")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/events")
def events():
    if not LOGFILE.exists():
        return jsonify([])
    lines = LOGFILE.read_text(encoding="utf-8", errors="ignore").splitlines()
    last = lines[-100:] if len(lines) > 100 else lines
    entries = []
    for line in last:
        try:
            data = json.loads(line)
            entries.append({
                "timestamp": data.get("timestamp", ""),
                "src_ip": data.get("src_ip", ""),
                "username": data.get("username", ""),
                "password": data.get("password", ""),
                "input": data.get("input", ""),
                "eventid": data.get("eventid", ""),
            })
        except json.JSONDecodeError:
            continue
    return jsonify(entries[::-1])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOF

cat << 'EOF' > "$HONEYPOT_DIR"/web/templates/index.html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Cowrie Honeypot Feed</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body { background: #111; color: #0f0; font-family: monospace; padding: 1rem; }
        .entry { margin-bottom: 1em; }
        .ip { color: #ff0; }
        .cmd { color: #0ff; }
    </style>
</head>
<body>
    <h1>Cowrie Honeypot Feed</h1>
    <div id="log"></div>
    <script>
    async function load() {
        try {
            const response = await fetch('/events');
            const data = await response.json();
            const log = document.getElementById('log');
            log.innerHTML = '';
            data.forEach(e => {
                const el = document.createElement('div');
                el.className = 'entry';
                el.innerHTML = `[${e.timestamp}] <span class="ip">${e.src_ip}</span> ${e.username}:${e.password} => <span class="cmd">${e.input || e.eventid}</span>`;
                log.appendChild(el);
            });
        } catch (err) {
            console.error(err);
        }
    }
    load();
    setInterval(load, 10000);
    </script>
</body>
</html>
EOF

echo "[+] Creando Dockerfile para visor web..."
cat << 'EOF' > "$HONEYPOT_DIR"/web/Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install flask
COPY app.py ./
COPY templates/ ./templates/
EXPOSE 5000
CMD ["python3", "app.py"]
EOF

echo "[+] Generando script de bloqueo automático por IP..."
cat << 'EOF' > "$HONEYPOT_DIR"/web/blocker.py
import json
import time
from pathlib import Path
from subprocess import run

SEEN = set()
LOGFILE = Path("/cowrie/data/json/cowrie.json")

while True:
    if LOGFILE.exists():
        for line in LOGFILE.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                data = json.loads(line)
                ip = data.get("src_ip")
                if ip and ip not in SEEN:
                    run(["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"])
                    SEEN.add(ip)
            except json.JSONDecodeError:
                continue
    time.sleep(10)
EOF

echo "[+] Generando docker-compose principal..."
cat << 'EOF' > "$HONEYPOT_DIR"/docker-compose.yml
services:
  cowrie:
    image: cowrie/cowrie:latest
    container_name: cowrie
    restart: unless-stopped
    ports:
      - "2222:2222"
    volumes:
      - "./data:/cowrie/data"
      - "./cfg/cowrie.cfg:/cowrie/etc/cowrie.cfg"
    networks:
      - honeynet
  web:
    build:
      context: ./web
    container_name: cowrie-web
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - "./data:/cowrie/data"
    networks:
      - honeynet

networks:
  honeynet:
    driver: bridge
    internal: true
EOF

cd "$HONEYPOT_DIR"
docker compose down
docker compose up -d --build
echo "[+] Esperando a que los servicios inicien"
sleep 5
docker compose ps
echo "[+] Honeypot desplegado"
echo "[+] Accede al visor en: http://localhost:5000"
echo "[+] Puedes iniciar el bloqueador con: docker exec -it cowrie-web python3 blocker.py"

echo -e "\033[1;32mGunicorn y honeypot en marcha.\033[0m"
echo -e "\033[1;35m\n¡Todos los procesos han terminado!\033[0m"

