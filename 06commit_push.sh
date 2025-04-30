#!/usr/bin/env bash
set -euo pipefail

# commit_push.sh
# Uso: ./commit_push.sh "Mensaje de commit" rama [remote]
# Ejemplo: ./commit_push.sh "Añade sistema de login" feature/login origin

# Comprobamos argumentos
if [[ $# -lt 2 ]]; then
  echo "Uso: $0 \"Mensaje de commit\" nombre-de-la-rama [remote]" >&2
  exit 1
fi

MSG="$1"
BRANCH="$2"
REMOTE="${3:-origin}"

# Agregar todos los cambios
git add .

# Crear el commit
git commit -m "$MSG"

# Hacer push al remoto y rama indicados
git push "$REMOTE" "$BRANCH"

