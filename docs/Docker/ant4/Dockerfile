# syntax=docker/dockerfile:1

# Base de Python
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye AS python-base

# Configuración de variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

LABEL author="markmur88" \
      description="Dockerfile for Debian Bullseye" \
      version="1.0"

# Configuración del directorio de trabajo
WORKDIR /app

# Actualización e instalación de paquetes esenciales
RUN apt update && apt upgrade -y && apt install -y --no-install-recommends \
    nodejs npm yarn \
    && apt autoremove -y && apt autoclean -y && rm -rf /var/lib/apt/lists/*

# Instalación de dependencias de Node.js
WORKDIR /app
COPY --link package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --production \
    && npm cache clean --force

# Instalación de dependencias de Python
RUN apt update && apt install -y --no-install-recommends \
    python3-venv python3-pip python3-dev python3-psycopg2-binary \
    && python3 -m venv .venv \
    && . .venv/bin/activate \
    && pip install --upgrade pip \
    && apt autoremove -y && apt autoclean -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN --mount=type=cache,target=/.cache/pip . .venv/bin/activate && pip install --no-cache-dir -r requirements.txt

# Configuración de Docker
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bullseye stable" > /etc/apt/sources.list.d/docker.list \
    && apt update && apt install -y docker-ce docker-ce-cli containerd.io \
    && usermod -aG docker ${USER}

# Configuración de SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords no/' /etc/ssh/sshd_config \
    && sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/#UsePAM yes/UsePAM no/' /etc/ssh/sshd_config \
    && sed -i 's/#X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config \
    && sed -i 's/#PrintMotd yes/PrintMotd no/' /etc/ssh/sshd_config \
    && mkdir -p /.ssh && touch /.ssh/authorized_keys \
    && chmod 700 /.ssh && chmod 600 /.ssh/authorized_keys

EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["sh", "-c", "python manage.py makemigrations && python manage.py migrate"]

# Etapa para Node.js
FROM node:23-bullseye AS node-base

# Configuración del directorio de trabajo
WORKDIR /app

# Copia de archivos necesarios para Node.js
COPY --link package.json package-lock.json ./

# Instalación de dependencias
RUN --mount=type=cache,target=/root/.npm npm ci --production \
    && npm cache clean --force

# Copia del resto de los archivos de la aplicación
COPY --link . .

# Comando para ejecutar la aplicación Node.js
CMD ["npm", "start"]
