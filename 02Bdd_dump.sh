#!/bin/bash
# BDD

export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

python3 manage.py makemigrations
python3 manage.py migrate
echo "  "
echo -e "\033[1mIniciando creación de datos de bdd.json\033[0m"

python3 manage.py dumpdata --indent 4 > bdd.json

echo "  "

echo -e "\033[1mDescarga de Base de datos LOCAL inicializada\033[0m"

echo "  "
