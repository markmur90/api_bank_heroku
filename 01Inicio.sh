#!/bin/bash
# Inicio

export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

#export DATABASE_URL="postgres://ue2erdhkle4v0h:pa1773a2b68d739e66a794acd529d1b60c016733f35be6884a9f541365d5922cf@ec2-63-33-30-239.eu-west-1.compute.amazonaws.com:5432/d9vb99r9t1m7kt"

source /home/markmur88/Documentos/Entorno/venvAPI/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py loaddata bdd.json
