#!/bin/bash
# Script de inicio

echo "Iniciando configuración del entorno..."
bash ./00Entorno.sh

echo "Configurando PostgreSQL..."
bash ./01Postgres.sh

echo "Inicializando base de datos..."
bash ./02Bdd.sh

echo "Inicializando Respaldos..."
bash ./copy_and_backup.sh

echo "Iniciando servidor con Gunicorn..."
bash ./03Gunicorn.sh
