#!/bin/bash

# === CONFIGURACIÓN INICIAL ===
ARCH=$(dpkg --print-architecture)
LOGFILE="/var/log/instalacion_kali_$(date +%Y%m%d_%H%M%S).log"
TEMP_KEY="/tmp/kali-key.asc"
KALI_KEY_URL="https://archive.kali.org/archive-key.asc"
EXPECTED_FINGERPRINT="ED444FF07D8D0BF6"

set -euo pipefail
exec > >(tee -a "$LOGFILE") 2>&1

# === VERIFICACIÓN DE ARQUITECTURA ===
if [[ "$ARCH" != "amd64" ]]; then
  echo "❌ Este script está diseñado solo para sistemas amd64. Se detectó: $ARCH"
  exit 1
fi

echo "💻 Arquitectura detectada: $ARCH"
echo "📅 Inicio de la instalación: $(date)"

# === IMPORTAR LLAVE DE KALI ===
echo "🔐 Descargando llave GPG de Kali..."
curl -fsSL "$KALI_KEY_URL" -o "$TEMP_KEY"
ACTUAL_FINGERPRINT=$(gpg --with-fingerprint --quiet "$TEMP_KEY" | grep -Eo "[A-F0-9]{16}" | head -n1)

if [[ "$ACTUAL_FINGERPRINT" != "$EXPECTED_FINGERPRINT" ]]; then
  echo "🚨 Fingerprint no coincide. Esperado: $EXPECTED_FINGERPRINT, Detectado: $ACTUAL_FINGERPRINT"
  exit 1
fi

echo "✅ Fingerprint verificado. Importando llave..."
gpg --dearmor "$TEMP_KEY" -o /usr/share/keyrings/kali-archive-keyring.gpg
cp /usr/share/keyrings/kali-archive-keyring.gpg /etc/apt/trusted.gpg.d/
chmod 644 /etc/apt/trusted.gpg.d/kali-archive-keyring.gpg
rm -f "$TEMP_KEY"

# === CONFIGURACIÓN DE IDIOMA Y TECLADO ===
echo "🌐 Configurando idioma y teclado..."
localectl set-locale LANG=es_ES.UTF-8
localectl set-keymap es
export LANG=es_ES.UTF-8

# === INSTALACIÓN DE HERRAMIENTAS GENERALES ===
echo "📦 Instalando herramientas generales..."
apt-get update
apt-get install -y curl gnupg2 lsb-release apt-transport-https ca-certificates software-properties-common

# === INSTALAR VS CODE ===
echo "💻 Instalando Visual Studio Code..."
temp_key=/tmp/packages.microsoft.gpg
curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > "$temp_key"
install -o root -g root -m 644 "$temp_key" /etc/apt/trusted.gpg.d/
echo "deb [arch=amd64] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list
apt-get update
apt-get install -y code
code --install-extension MS-CEINTL.vscode-language-pack-es --force || true

# === IDIOMA DEL SISTEMA ===
echo "🈸 Instalando paquetes de idioma..."
apt-get install -y language-pack-es
update-locale LANG=es_ES.UTF-8

# === FIREWALL ===
echo "🛡️ Configurando y habilitando UFW con políticas seguras..."
apt-get install -y ufw

# Reglas por defecto
ufw default deny incoming
ufw default allow outgoing
ufw logging full

# Habilitar el firewall
ufw --force enable

echo "✅ UFW configurado: todo entrante DENEGADO, saliente PERMITIDO, logging activado."

# === BASE DE DATOS ===
echo "🗄️ Instalando PostgreSQL..."
apt-get install -y postgresql postgresql-contrib

# === DOCKER ===
echo "🐳 Instalando Docker..."
curl -fsSL https://get.docker.com | sh
usermod -aG docker "$USER"

# === GITHUB DESKTOP ===
echo "🐙 Instalando GitHub Desktop..."
wget https://github.com/shiftkey/desktop/releases/download/release-3.3.4-linux1/GitHubDesktop-linux-3.3.4-linux1.deb -O /tmp/github-desktop.deb
apt-get install -y /tmp/github-desktop.deb || apt-get --fix-broken install -y

# === TELEGRAM DESKTOP ===
echo "💬 Instalando Telegram Desktop..."
tg_url=https://telegram.org/dl/desktop/linux
wget -O /tmp/tg.tar.xz "$tg_url"
mkdir -p ~/.local/share/telegram
tar -xf /tmp/tg.tar.xz -C ~/.local/share/telegram

# === PYTHON Y DJANGO ===
echo "🐍 Instalando Python y Django..."
apt-get install -y python3 python3-pip
pip3 install --upgrade pip
pip3 install django

# === SSH ===
echo "🔐 Instalando herramientas SSH..."
apt-get install -y openssh-client openssh-server

# === FUERZA BRUTA ===
echo "💣 Instalando herramientas de fuerza bruta..."
apt-get install -y medusa hydra

# === DNS ===
echo "🌐 Instalando herramientas DNS..."
apt-get install -y dnsutils dnsenum

# === PROTONVPN ===
echo "🛡️ Instalando ProtonVPN CLI..."
apt-get install -y python3-pip openvpn dialog
pip3 install protonvpn-cli
protonvpn init || echo "🔧 Configuración de ProtonVPN pendiente."

# === HEROKU CLI ===
echo "🚀 Instalando Heroku CLI..."
curl https://cli-assets.heroku.com/install-ubuntu.sh | sh

# === ACTUALIZACIÓN FINAL ===
echo "🔄 Actualizando el sistema..."
apt-get update && apt-get full-upgrade -y
apt-get autoremove -y
apt-get autoclean -y

echo "✅ Instalación COMPLETADA con éxito."
echo "📁 Revisa el log en: $LOGFILE"
