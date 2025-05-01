#!/bin/bash
# Script de inicio

echo -e "\n\033[1;34m🔧 **\033[1;4;34mIniciando configuración del entorno...\033[0m**\033[0m"
read -p "¿Desea ejecutar 00Entorno.sh? (s/n): " respuesta
if [[ "$respuesta" == "s" ]]; then
    bash ./00Entorno.sh
fi
echo " "

echo -e "\n\033[1;34m🐘 **\033[1;4;34mConfigurando PostgreSQL...\033[0m**\033[0m"
read -p "¿Desea ejecutar 01Postgres.sh? (s/n): " respuesta
if [[ "$respuesta" == "s" ]]; then
    bash ./01Postgres.sh
fi
echo " "

echo -e "\n\033[1;34m📂 **\033[1;4;34mInicializando base de datos...\033[0m**\033[0m"
read -p "¿Desea ejecutar 02Bdd.sh? (s/n): " respuesta
if [[ "$respuesta" == "s" ]]; then
    bash ./02Bdd.sh
fi
echo " "

echo -e "\n\033[1;34m💾 **\033[1;4;34mInicializando Respaldos...\033[0m**\033[0m"
read -p "¿Desea ejecutar 03copy_and_backup.sh? (s/n): " respuesta
if [[ "$respuesta" == "s" ]]; then
    bash ./03copy_and_backup.sh
fi
echo " "

echo -e "\n\033[1;34m🌐 **\033[1;4;34mSincronizando con remoto...\033[0m**\033[0m"
read -p "¿Desea ejecutar 04sync_to_remote.sh? (s/n): " respuesta
if [[ "$respuesta" == "s" ]]; then
    bash ./04sync_to_remote.sh
fi
echo " "

echo -e "\n\033[1;34m🚀 **\033[1;4;34mIniciando servidor con Gunicorn...\033[0m**\033[0m"
read -p "¿Desea ejecutar 05Gunicorn.sh? (s/n): " respuesta
if [[ "$respuesta" == "s" ]]; then
    bash ./05Gunicorn.sh
fi
