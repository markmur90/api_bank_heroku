#!/bin/bash
# Inicio

python3 -m venv ~/Documentos/Entorno/venvAPI
source ~/Documentos/Entorno/venvAPI/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt
python3 manage.py collectstatic --noinput

echo "✅ ✅ ✅ Environment setup complete. You can now run your Django application.✅ ✅ ✅ "

