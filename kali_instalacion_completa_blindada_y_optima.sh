#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

# === CONFIGURACIÓN INICIAL ===
ARCH=$(dpkg --print-architecture)
LOGFILE="/var/log/instalacion_kali_$(date +%Y%m%d_%H%M%S).log"
TEMP_KEY="/tmp/kali-key.asc"
KALI_KEY_URL="https://archive.kali.org/archive-key.asc"
EXPECTED_FINGERPRINT="ED444FF07D8D0BF6"
BACKUP_DIR="/etc/apt/backup_lists_$(date +%Y%m%d_%H%M%S)"

set -euo pipefail
exec > >(tee -a "$LOGFILE") 2>&1

echo "📋 Iniciando instalación. Log: $LOGFILE"

# === VERIFICAR ARQUITECTURA ===
if [[ "$ARCH" != "amd64" ]]; then
  echo "❌ Este script es solo para sistemas amd64. Detectado: $ARCH"
  exit 1
fi

# === BACKUP DE ARCHIVOS APT ===
echo "🗂️ Backup de APT..."
mkdir -p "$BACKUP_DIR"
cp -r /etc/apt/sources.list* "$BACKUP_DIR" || true
cp -r /etc/apt/sources.list.d "$BACKUP_DIR" || true

# === REPARACIÓN DE DPKG Y LOCKS ===
echo "🧰 Reparando DPKG..."
rm -f /var/lib/apt/lists/lock /var/cache/apt/archives/lock /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend
dpkg --configure -a || true
apt-get install -f -y || true

# === IMPORTACIÓN DE LLAVE DE KALI ===
echo "🔐 Importando llave de Kali..."
curl -fsSL "$KALI_KEY_URL" -o "$TEMP_KEY"
ACTUAL_FINGERPRINT=$(gpg --with-fingerprint --quiet "$TEMP_KEY" | grep -Eo "[A-F0-9]{16}" | head -n1)
if [[ "$ACTUAL_FINGERPRINT" != "$EXPECTED_FINGERPRINT" ]]; then
  echo "🚨 Fingerprint inválido: $ACTUAL_FINGERPRINT. Esperado: $EXPECTED_FINGERPRINT"
  exit 1
fi
gpg --dearmor "$TEMP_KEY" -o /usr/share/keyrings/kali-archive-keyring.gpg
cp /usr/share/keyrings/kali-archive-keyring.gpg /etc/apt/trusted.gpg.d/
chmod 644 /etc/apt/trusted.gpg.d/kali-archive-keyring.gpg
rm -f "$TEMP_KEY"

# === CONFIGURACIÓN DE IDIOMA Y TECLADO ===
echo "🌐 Configurando idioma y teclado..."
localectl set-locale LANG=es_ES.UTF-8
localectl set-keymap es
export LANG=es_ES.UTF-8

# === INSTALACIÓN DE PAQUETES GENERALES ===
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

# === PAQUETES DE IDIOMA ===
echo "🈸 Instalando paquete de idioma español..."
apt-get install -y language-pack-es
update-locale LANG=es_ES.UTF-8

# === FIREWALL (UFW) ===
echo "🛡️ Configurando UFW..."
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw logging full
ufw --force enable

# === POSTGRESQL ===
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
echo "🔐 Instalando SSH..."
apt-get install -y openssh-client openssh-server

# === FUERZA BRUTA ===
echo "💣 Instalando herramientas de fuerza bruta..."
apt-get install -y medusa hydra

# === DNS ===
echo "🌐 Instalando herramientas DNS..."
apt-get install -y dnsutils dnsenum

# === PROTONVPN ===
echo "🛡️ Instalando ProtonVPN..."
apt-get install -y python3-pip openvpn dialog
pip3 install protonvpn-cli
protonvpn init || echo "⚠️ ProtonVPN requiere configuración manual posterior."

echo "🚀 Instalando Heroku CLI..."
curl https://cli-assets.heroku.com/install-ubuntu.sh | sh

echo "🔄 Aplicando actualización final del sistema..."
apt-get update && apt-get full-upgrade -y
apt-get autoremove -y
apt-get autoclean -y

# === OPTIMIZACIÓN DE USO DE MEMORIA ===
echo "🧠 Optimizando uso de memoria..."

# swappiness bajo
sysctl vm.swappiness=10
echo "vm.swappiness=10" >> /etc/sysctl.conf

# liberar cachés
sync; echo 3 > /proc/sys/vm/drop_caches

# zRAM condicional si tienes <8GB
TOTAL_RAM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
if [[ "$TOTAL_RAM" -lt 8000000 ]]; then
  echo "🌀 Activando zRAM (sistema con <8GB de RAM)..."
  apt-get install -y zram-tools
  systemctl enable zramswap
  systemctl start zramswap
else
  echo "⚡ Suficiente RAM detectada. No se activa zRAM."
fi

# mostrar estado de memoria
echo "📊 Estado final de memoria:"
free -h

# === LIMPIEZA FINAL ===
apt-get autoremove -y
apt-get autoclean -y

echo "✅ Instalación y configuración COMPLETADAS con éxito."
echo "📁 Backup de APT en: $BACKUP_DIR"
echo "📄 Log completo en: $LOGFILE"
