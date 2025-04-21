#!/bin/bash
set -e

# 1. Actualizar el sistema
sudo apt update && sudo apt full-upgrade -y

# 2. Agregar repositorio bullseye (Debian estable)
echo "deb http://deb.debian.org/debian bullseye main contrib non-free" | sudo tee /etc/apt/sources.list.d/bullseye.list
sudo apt update

# 3. Instalar herramientas generales
sudo apt install -y curl gnupg2 lsb-release apt-transport-https ca-certificates software-properties-common

# 4. Instalar Visual Studio Code
temp_key=/tmp/packages.microsoft.gpg
curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > "$temp_key"
sudo install -o root -g root -m 644 "$temp_key" /etc/apt/trusted.gpg.d/
echo "deb [arch=amd64] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list
sudo apt update
sudo apt install -y code

# Instalar extensión idioma español para VSCode
code --install-extension MS-CEINTL.vscode-language-pack-es --force || true

# 5. Configurar idioma español
sudo apt install -y language-pack-es
sudo update-locale LANG=es_ES.UTF-8

# 6. Instalar y habilitar ufw
sudo apt install -y ufw
sudo ufw enable

# 7. Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 8. Instalar Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"

# 9. Instalar GitHub Desktop (a través de .deb unofficial)
wget https://github.com/shiftkey/desktop/releases/download/release-3.3.4-linux1/GitHubDesktop-linux-3.3.4-linux1.deb -O /tmp/github-desktop.deb
sudo apt install -y /tmp/github-desktop.deb || sudo apt --fix-broken install -y

# 10. Instalar Telegram
tg_url=https://telegram.org/dl/desktop/linux
wget -O /tmp/tg.tar.xz "$tg_url"
mkdir -p ~/.local/share/telegram
tar -xf /tmp/tg.tar.xz -C ~/.local/share/telegram

# 11. Instalar Python y Django
sudo apt install -y python3 python3-pip
pip3 install --upgrade pip
pip3 install django

# 12. Herramientas para SSH
sudo apt install -y openssh-client openssh-server

# 13. Herramientas de fuerza bruta
sudo apt install -y medusa hydra

# 14. Herramientas para DNS
sudo apt install -y dnsutils dnsenum

# 15. Instalar ProtonVPN
sudo apt install -y python3-pip openvpn dialog
pip3 install protonvpn-cli
sudo protonvpn init

# 16. Instalar Heroku CLI
curl https://cli-assets.heroku.com/install-ubuntu.sh | sh

# 17. Actualizar el sistema
sudo apt update && sudo apt full-upgrade -y

echo "\n✅ Instalación completada. Reinicia tu sesión para aplicar todos los cambios."
