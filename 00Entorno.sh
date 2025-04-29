#!/bin/bash
# Inicio


python3 -m venv $HOME/Documentos/Entorno/venvAPI

echo " ------------------------------------------- " 

source $HOME/Documentos/Entorno/venvAPI/bin/activate

echo " ------------------------------------------- " 

pip3 install -r $HOME/Documentos/GitHub/api_bank_h/requirements.txt

echo " ------------------------------------------- " 

sudo systemctl enable postgresql

echo " ------------------------------------------- " 

sudo systemctl start postgresql

echo " ------------------------------------------- " 

# sudo systemctl status postgresql

clear

echo -e "\033[1m✅ ✅ ✅ Environment setup complete. You can now run your Django application.✅ ✅ ✅\033[0m"

