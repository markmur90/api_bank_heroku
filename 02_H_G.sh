#!/usr/bin/env bash
set -euo pipefail
export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"
PROJECT_ROOT="$HOME/Documentos/GitHub/api_bank_h2"
VENV_PATH="$HOME/Documentos/Entorno/venvAPI"
INTERFAZ="wlan0"

confirmar() {
    echo ""
    echo ""
    printf "\033[1;34m¿Deseas ejecutar: %s? (s/n):\033[0m " "$1"
    read -r resp
    [[ "$resp" == "s" || -z "$resp" ]]
}

clear

for PUERTO in 2222 8000 5000 8001 35729; do
    if lsof -i tcp:"$PUERTO" &>/dev/null; then
        if confirmar "Cerrar procesos en puerto $PUERTO"; then
            sudo fuser -k "${PUERTO}"/tcp || true
            echo -e "\033[1;32mPuerto $PUERTO liberado.\033[0m"
        fi
    fi
done

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

if confirmar "Iniciar Gunicorn, honeypot y livereload simultáneamente"; then
    clear
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
                echo "Liberando puerto $port..."
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
            echo "Liberando puerto $port..."
            echo ""
            echo ""
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

echo -e "\033[1;35m\n¡Todos los procesos han terminado!\033[0m"