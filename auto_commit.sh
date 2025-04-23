#!/bin/bash

# Generar un mensaje de commit basado en los cambios
CHANGES=$(git diff --cached --name-only | xargs -I {} echo "- Modificado: {}")
if [ -z "$CHANGES" ]; then
  echo "No hay cambios para commitear."
  exit 0
fi

# Crear un mensaje de commit
COMMIT_MESSAGE="Actualización automática:
$CHANGES"

# Agregar todos los cambios
git add .

# Realizar el commit
git commit -m "$COMMIT_MESSAGE"

# Subir los cambios al repositorio remoto
git push origin $(git rev-parse --abbrev-ref HEAD)