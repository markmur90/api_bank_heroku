#!/bin/bash
# Runserver
export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

source .venv/bin/activate
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py runserver


