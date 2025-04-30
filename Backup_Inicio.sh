#!/bin/bash
# Script de inicio

echo "Iniciando configuración del entorno..."
bash ./00Entorno.sh
echo " "
echo "Configurando PostgreSQL..."
bash ./01Postgres.sh
echo " "
echo "Inicializando base de datos..."
bash ./02Bdd.sh
echo " "
echo "Inicializando Respaldos..."
bash ./copy_and_backup.sh
echo " "
echo "Espaldo WEB..."
bash ./sync_to_remote.sh
echo " "
echo "Iniciando servidor con Gunicorn..."
bash ./03Gunicorn.sh
