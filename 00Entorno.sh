#!/bin/bash
# Inicio

export DATABASE_URL="postgres://markmur88:Ptf8454Jd55@localhost:5432/mydatabase"

python3 -m venv $HOME/Documentos/Entorno/venvAPI
source $HOME/Documentos/Entorno/venvAPI/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements.txt
python3 manage.py collectstatic --noinput
clear
echo "✅ ✅ ✅ Environment setup complete. You can now run your Django application.✅ ✅ ✅ "


