#!/bin/bash

# === Variables ===
ARCH=$(dpkg --print-architecture)
LOGFILE="/var/log/actualizacion_kali_$(date +%Y%m%d_%H%M%S).log"
KALI_KEY_URL="https://archive.kali.org/archive-key.asc"

# === Verificar arquitectura ===
if [[ "$ARCH" != "amd64" ]]; then
  echo "❌ Este script está diseñado solo para sistemas amd64. Se detectó: $ARCH" | tee -a "$LOGFILE"
  exit 1
fi

# === Redirigir salida a log ===
set -euo pipefail
exec > >(tee -a "$LOGFILE") 2>&1

echo "💻 Arquitectura detectada: $ARCH"
echo "📅 Inicio de la actualización: $(date)"

echo "🔐 Importando llave GPG de Kali..."
curl -fsSL "$KALI_KEY_URL" | gpg --dearmor -o /usr/share/keyrings/kali-archive-keyring.gpg

echo "📝 Verificando y agregando llave al sistema..."
cp /usr/share/keyrings/kali-archive-keyring.gpg /etc/apt/trusted.gpg.d/
chmod 644 /etc/apt/trusted.gpg.d/kali-archive-keyring.gpg

echo "🔍 Limpiando locks antiguos..."
rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/cache/apt/archives/lock

echo "🔄 Actualizando lista de paquetes..."
apt-get update

echo "⬆️ Realizando upgrade de paquetes..."
apt-get upgrade -y

echo "⏫ Realizando dist-upgrade..."
apt-get dist-upgrade -y

echo "🧼 Limpiando paquetes innecesarios..."
apt-get autoremove -y
apt-get autoclean -y

echo "✅ Actualización finalizada sin errores."
echo "📁 Log disponible en: $LOGFILE"
echo "📅 Fin del proceso: $(date)"
