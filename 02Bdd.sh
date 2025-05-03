#!/bin/bash
# BDD

export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

python3 manage.py makemigrations
python3 manage.py migrate
echo "  "
echo -e "\033[1mIniciando subida de datos de bdd.json\033[0m"

python3 manage.py loaddata bdd.json

echo "  "

echo -e "\033[1mSubida de datos LOCAL completada.\033[0m"

echo "  "
