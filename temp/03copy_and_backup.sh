#!/bin/bash

# Ruta de origen y destino para la copia del proyecto
SOURCE="$HOME/Documentos/GitHub/api_bank_h2/"
DEST="/home/markmur88/Documentos/GitHub/api_bank_heroku/"

# Ruta de destino para la copia de seguridad en formato ZIP
BACKUP_DIR="/home/markmur88/Documentos/GitHub/backup/"
BACKUP_ZIP="${BACKUP_DIR}$(date +%Y%m%d__%H-%M-%S)_backup_api_bank_h2.zip"

echo " "
# Confirmar antes de proceder con la copia del proyecto
echo -e "\033[1m¿Desea proceder con la copia del proyecto? (s/n):\033[0m"
read -r CONFIRM
PROJECT_COPIED=false
if [[ "$CONFIRM" != "s" ]]; then
    echo " "
    echo "Operación cancelada. Continuando con la copia de seguridad..."
else
    # Crear el directorio de destino si no existe
    mkdir -p "$DEST"
    # Copiar archivos excluyendo .gitattributes, .gitignore y la carpeta .git
    rsync -av --exclude=".gitattributes" --exclude=".gitignore" --exclude="auto_commit_sync.sh" --exclude=".git/" "$SOURCE" "$DEST"
    echo " "
    echo -e "\033[1mProyecto copiado exitosamente a:\033[0m"
    echo "$DEST"
    PROJECT_COPIED=true
fi

# Pausa antes de proceder con la copia de seguridad
sleep 1
echo " "

# Confirmar antes de proceder con la copia de seguridad
echo -e "\033[1m¿Desea proceder con la copia de seguridad? (s/n):\033[0m"
read -r CONFIRM
BACKUP_CREATED=false
if [[ "$CONFIRM" == "s" ]]; then
    # Crear el directorio de copia de seguridad si no existe
    mkdir -p "$BACKUP_DIR"

    echo " "
    # Solicitar si se desea agregar un campo adicional al nombre del archivo ZIP
    echo -e "\033[1m¿Desea agregar un campo adicional al nombre del archivo ZIP? (s/n):\033[0m"
    read -r ADD_FIELD
    if [[ "$ADD_FIELD" == "s" ]]; then
        echo " "
        echo -e "\033[1mIngrese el campo adicional:\033[0m"
        read -r EXTRA_FIELD
        BACKUP_ZIP="${BACKUP_DIR}$(date +%Y%m%d__%H-%M-%S)_backup_api_bank_h2_${EXTRA_FIELD}.zip"
    fi
    echo " "

    # Realizar la copia de seguridad en formato ZIP excluyendo archivos y carpetas específicos
    echo -e "\033[1mCreando archivo ZIP de respaldo...\033[0m"
    cd "$SOURCE" || exit
    zip -r "$BACKUP_ZIP" . -x ".gitattributes" ".gitignore" "auto_commit_sync.sh" ".git/*" | pv
    echo " "
    echo -e "\033[1mCopia de seguridad creada exitosamente en:\033[0m"
    echo "$BACKUP_ZIP"
    BACKUP_CREATED=true
fi

# Mensaje final
echo " "
if $PROJECT_COPIED && $BACKUP_CREATED; then
    echo -e "\033[1mAmbos procesos se realizaron exitosamente:\033[0m"
    echo -e "\033[1m- Proyecto copiado a:\033[0m $DEST"
    echo -e "\033[1m- Archivo ZIP de respaldo creado en:\033[0m $BACKUP_ZIP"
elif $PROJECT_COPIED; then
    echo -e "\033[1mEl proyecto fue copiado exitosamente a:\033[0m"
    echo "$DEST"
    echo -e "\033[1mEl archivo ZIP de respaldo no fue creado.\033[0m"
elif $BACKUP_CREATED; then
    echo -e "\033[1mEl archivo ZIP de respaldo fue creado exitosamente en:\033[0m"
    echo "$BACKUP_ZIP"
    echo -e "\033[1mEl proyecto no fue copiado.\033[0m"
else
    echo -e "\033[1mNinguno de los procesos se realizó.\033[0m"
fi
echo " "


