# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye AS python-base

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

LABEL author="markmur88" \
      description="Dockerfile for Debian Bullseye" \
      version="1.0"

WORKDIR /app

RUN apt update && apt upgrade -y && apt install -y --no-install-recommends \
    nodejs npm yarn python3-venv python3-pip python3-dev python3-psycopg2-binary \
    && apt autoremove -y && apt autoclean -y && rm -rf /var/lib/apt/lists/*

# Crear el usuario markmur con UID y GID específicos
RUN useradd -ms /bin/bash -u 1000 -U markmur && echo "markmur:Ptf8454Jd55" | chpasswd && adduser markmur sudo

# Cambiar al usuario markmur
USER markmur:markmur

# Asegurar que el entorno esté activado al iniciar
RUN echo "cd /app && . .venv/bin/activate" >> /home/markmur/.bashrc

COPY --link package.json package-lock.json ./
RUN npm ci --production && npm cache clean --force

RUN python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip

COPY requirements.txt ./
RUN . .venv/bin/activate && pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido del proyecto al contenedor
COPY --link . .

EXPOSE 8000

# Etapa para Node.js
FROM node:23-bullseye AS node-base

# Configuración del directorio de trabajo
WORKDIR /app

# Copia de archivos necesarios para Node.js
COPY --link package.json package-lock.json ./

# Instalación de dependencias
RUN --mount=type=cache,target=/root/.npm npm ci --production \
    && npm cache clean --force


