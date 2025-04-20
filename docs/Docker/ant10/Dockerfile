# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye AS python-base

# Configuración de variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

LABEL author="markmur88" \
      description="Dockerfile for Debian Bullseye" \
      version="1.0"

# Establecer el directorio de trabajo
WORKDIR /app

# Actualización e instalación de dependencias necesarias
RUN apt update && apt upgrade -y && apt install -y --no-install-recommends \
    nodejs npm yarn python3-venv python3-pip python3-dev python3-psycopg2-binary \
    && apt autoremove -y && apt autoclean -y && rm -rf /var/lib/apt/lists/*

# Copiar archivos necesarios para instalar dependencias
COPY package.json package-lock.json requirements.txt ./

# Instalación de dependencias de Node.js
RUN npm ci --production && npm cache clean --force

# Configuración del entorno virtual de Python
RUN python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Crear el usuario markmur con UID y GID específicos
RUN useradd -m -u 1000 -s /bin/bash markmur && adduser markmur sudo

# Cambiar al usuario markmur
USER markmur:markmur

# Copiar el resto del proyecto al contenedor
COPY . .

# Exponer el puerto 8000
EXPOSE 8000

# Comando por defecto para iniciar en la carpeta del contenedor
CMD ["bash", "-c", "cd /app && exec bash"]