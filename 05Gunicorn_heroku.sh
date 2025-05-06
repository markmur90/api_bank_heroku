#!/usr/bin/env bash
set -euo pipefail

export DATABASE_URL="postgres://ue2erdhkle4v0h:pa1773a2b68d739e66a794acd529d1b60c016733f35be6884a9f541365d5922cf@ec2-63-33-30-239.eu-west-1.compute.amazonaws.com:5432/d9vb99r9t1m7kt"

clear

echo "  "
# Cerrar procesos en los puertos especificados antes de continuar
for PUERTO in 8000; do
    if lsof -i tcp:"$PUERTO" &>/dev/null; then
        echo -e "\033[1;33mDetectado proceso en el puerto $PUERTO.\033[0m"
        sudo fuser -k "${PUERTO}"/tcp || true
        echo -e "\033[1;32mPuerto $PUERTO liberado.\033[0m"
    fi
done

echo "  "

# Realizar las migraciones y otras tareas

pip3 install -r requirements.txt


python3 manage.py makemigrations

echo "  "

python3 manage.py migrate

echo "  "

python3 manage.py collectstatic --noinput

echo "  "

clear
echo -e "\033[1mServidor en ejecución\033[0m"
echo " "
gunicorn config.wsgi:application --bind 0.0.0.0:8000