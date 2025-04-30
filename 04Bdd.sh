#!/bin/bash
# BDD

export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

python3 manage.py makemigrations
python3 manage.py migrate

#python3 manage.py createsuperuser
python3 manage.py loaddata bdd.json


echo -e "\033[1mBase de datos LOCAL inicializada\033[0m"

