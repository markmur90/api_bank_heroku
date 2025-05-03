#!/usr/bin/env bash
set -euo pipefail

export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

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

if confirmar "Puesta en marcha de Gunicorn y apertura en Mozilla"; then
    echo -e "\033[1;34m🚀 Iniciando Gunicorn...\033[0m"
    python3 manage.py collectstatic --noinput
    nohup gunicorn config.wsgi:application --bind 0.0.0.0:8000 > gunicorn.log 2>&1 &
    echo -e "\033[1;34m🌐 Abriendo Mozilla...\033[0m"
    mozilla --new-tab http://localhost:5000 --new-tab http://localhost:8000 &
    echo -e "\033[32m✅ Gunicorn y navegador listos.\033[0m"
fi