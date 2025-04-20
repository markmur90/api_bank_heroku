# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye AS python-base

# Configuración de variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

LABEL author="markmur88" \
      description="Dockerfile for Debian Bullseye" \
      version="1.0"

# Actualización e instalación de paquetes esenciales
RUN apt update && apt upgrade -y && apt install -y --no-install-recommends \
    python3 python3-venv python3-pip python3-dev python3-psycopg2 python3-psycopg2-binary \
    git curl wget gcc libffi-dev libssl-dev nodejs npm yarn nginx supervisor \
    postgresql postgresql-client libpq-dev \
    sudo openssh-server apt-transport-https ca-certificates software-properties-common \
    && apt autoremove -y && apt autoclean -y && rm -rf /var/lib/apt/lists/*

# Configuración de usuario
RUN useradd -m -s /bin/bash markmur88 && echo "markmur88:Ptf8454Jd55" | chpasswd \
    && usermod -aG sudo,docker markmur88  # Añadido grupo docker para evitar redundancia

USER markmur88

# Configuración de Docker
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bullseye stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt update && apt install -y docker-ce docker-ce-cli containerd.io \
    && sudo usermod -aG docker markmur88

# Configuración de SSH
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords no/' /etc/ssh/sshd_config \
    && sed -i 's/#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config \
    && sed -i 's/#UsePAM yes/UsePAM no/' /etc/ssh/sshd_config \
    && sed -i 's/#X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config \
    && sed -i 's/#PrintMotd yes/PrintMotd no/' /etc/ssh/sshd_config \
    && sed -i 's/#AuthorizedKeysFile/AuthorizedKeysFile/' /etc/ssh/sshd_config \
    && mkdir -p /home/markmur88/.ssh && touch /home/markmur88/.ssh/authorized_keys \
    && chmod 700 /home/markmur88/.ssh && chmod 600 /home/markmur88/.ssh/authorized_keys

# Configuración del directorio de trabajo
WORKDIR /app

# Instalación de dependencias de Python
COPY requirements.txt ./
RUN --mount=type=cache,target=/home/markmur88/.cache/pip pip install --upgrade pip  # Añadido para actualizar pip \
    && pip install --no-cache-dir -r requirements.txt

# Copia del código de la aplicación
COPY . ./

# Exposición del puerto de la aplicación
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

# Configuración de usuario no root
RUN useradd -m appuser
USER appuser

# Comando para ejecutar la aplicación Node.js
CMD ["npm", "start"]
