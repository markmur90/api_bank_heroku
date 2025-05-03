#!/bin/bash
# Script de inicio

echo ""

echo -e "\n\033[1;34m🔧 **\033[1;4;34mIniciando configuración del entorno...\033[0m**\033[0m"
echo ""
read -p "¿Desea ejecutar 00Entorno.sh? (s/n): " respuesta
echo " "
if [[ "$respuesta" == "s" ]]; then
    bash ./00Entorno.sh
fi
echo " "
echo " "
echo " "
echo -e "\n\033[1;34m💾 **\033[1;4;34mInicializando Creación de respaldo de datos de base de datos...\033[0m**\033[0m"
echo ""
read -p "¿Desea ejecutar 02Bdd_dump.sh? (s/n): " respuesta
echo " "
if [[ "$respuesta" == "s" ]]; then
    bash ./02Bdd_dump.sh
fi
echo " "
echo " "
echo " "
echo -e "\n\033[1;34m👤 **\033[1;4;34mInicializando Creación de Super User...\033[0m**\033[0m"
echo ""
read -p "¿Desea ejecutar 02user.sh? (s/n): " respuesta
echo " "
if [[ "$respuesta" == "s" ]]; then
    bash ./01Postgres.sh
    bash ./02user.sh
fi
echo " "
echo " "
echo " "
echo -e "\n\033[1;34m📤 **\033[1;4;34mInicializando subida de datos en base de datos...\033[0m**\033[0m"
echo ""
read -p "¿Desea ejecutar 02Bdd.sh? (s/n): " respuesta
echo " "
if [[ "$respuesta" == "s" ]]; then
    bash ./01Postgres.sh
    bash ./02Bdd.sh
fi
echo " "
echo " "
echo " "
echo -e "\n\033[1;34m🗂️ **\033[1;4;34mInicializando Respaldos HEROKU, SQL y ZIP...\033[0m**\033[0m"
echo ""
read -p "¿Desea ejecutar 03copy_and_backup.sh? (s/n): " respuesta
echo " "
if [[ "$respuesta" == "s" ]]; then
    bash ./03copy_and_backup.sh
fi
echo " "
echo " "
echo " "
echo -e "\n\033[1;34m🔄 **\033[1;4;34mSincronizando con remoto...\033[0m**\033[0m"
echo ""
read -p "¿Desea ejecutar 04sync_to_remote.sh? (s/n): " respuesta
echo " "
if [[ "$respuesta" == "s" ]]; then
    bash ./06sync_to_remote.sh
fi
echo " "
echo " "
echo " "
echo -e "\n\033[1;34m🚀 **\033[1;4;34mIniciando servidor con Gunicorn...\033[0m**\033[0m"
echo ""
read -p "¿Desea ejecutar 05Gunicorn.sh? (s/n): " respuesta
echo " "
if [[ "$respuesta" == "s" ]]; then
    bash ./05Gunicorn.sh
fi
