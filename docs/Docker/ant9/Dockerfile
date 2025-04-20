# syntax=docker/dockerfile:1

FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye AS python-base

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

LABEL author="markmur88" \
      description="Dockerfile for Debian Bullseye" \
      version="1.0"

WORKDIR /app

# Copia todo el contenido del proyecto al contenedor
COPY . .

RUN apt update && apt upgrade -y && apt install -y --no-install-recommends \
    nodejs npm yarn python3-venv python3-pip python3-dev \
    && apt autoremove -y && apt autoclean -y && rm -rf /var/lib/apt/lists/*

COPY --link package.json package-lock.json ./
RUN npm ci --production && npm cache clean --force

RUN python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip

COPY requirements.txt ./
RUN . .venv/bin/activate && pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]


