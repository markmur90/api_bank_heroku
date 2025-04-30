#!/bin/bash
# Gunicorn

export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

source $HOME/Documentos/Entorno/venvAPI/bin/activate

echo "  "

python3 manage.py makemigrations

echo "  "

python3 manage.py migrate

echo "  "

python3 manage.py collectstatic --noinput

echo "  "


echo -e "\033[1mServidor en ejecución\033[0m"
echo " "
gunicorn config.wsgi:application --bind 0.0.0.0:8000
