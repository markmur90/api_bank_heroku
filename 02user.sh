#!/bin/bash
# BDD

export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

python3 manage.py makemigrations
python3 manage.py migrate
echo "  "
echo -e "\033[1mIniciando Creación de Super User\033[0m"

python3 manage.py createsuperuser

echo "  "

echo -e "\033[1mCreación de Super User Completa\033[0m"

echo "  "
