#!/bin/bash

# Ruta del repositorio que deseas monitorizar
REPO_PATH=$(eval echo ~/Documentos/GitHub/api_bank_heroku)
LOGS_PATH=$(eval echo ~/Documentos/GitHub/logs/api_bank_heroku)
cd "$REPO_PATH" || exit 1

# Archivo de log para registrar eventos
LOG_FILE="$LOGS_PATH/commit_sync.log"

# Función para generar un mensaje de commit automáticamente con detalles de los cambios
generate_commit_message() {
    # Obtener la fecha y hora actual
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Lista de archivos modificados
    FILES_CHANGED=$(git diff --name-only)
    
    # Inicializa el mensaje de commit
    COMMIT_MESSAGE="Cambios realizados el $TIMESTAMP:\n"

    # Detalla los cambios por archivo
    for FILE in $FILES_CHANGED; do
        # Obtiene un resumen del diff para el archivo
        DIFF_SUMMARY=$(git diff --stat -- "$FILE")
        
        # Agrega un resumen al mensaje de commit
        COMMIT_MESSAGE+="\nArchivo: $FILE\n$DIFF_SUMMARY\n"
    done

    echo -e "$COMMIT_MESSAGE"
}

# Detectar cambios en el repositorio
CHANGES=$(git status --porcelain)

# Verificar si hay cambios
if [ -n "$CHANGES" ]; then
    echo "Cambios detectados. Realizando commit y sincronización..."
    git add -A
    COMMIT_MESSAGE=$(generate_commit_message)
    git commit -m "$COMMIT_MESSAGE"
    git push origin "$(git rev-parse --abbrev-ref HEAD)"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Commit y sincronización realizados." >> "$LOG_FILE"
else
    echo "No se detectaron cambios. Registrando en el log..."
    echo "$(date '+%Y-%m-%d %H:%M:%S') - No se detectaron cambios. No se realizó ningún commit." >> "$LOG_FILE"
fi