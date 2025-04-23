FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

ENV PYTHONUNBUFFERED=1
ENV markmur88cpwd=Ptf8454Jd55

# Crear usuario y agregarlo a los grupos necesarios
RUN groupadd docker && groupadd postgres && \
    useradd -m -s /bin/bash markmur88 && \
    echo "markmur88:${markmur88cpwd}" | chpasswd && \
    usermod -aG sudo,docker,postgres,root markmur88

USER markmur88

# Instalar dependencias del sistema (como root)
USER root
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip python3-dev \
    postgresql postgresql-contrib \
    curl build-essential \
    nodejs npm yarn \
    && apt-get autoremove -y && apt-get autoclean -y && rm -rf /var/lib/apt/lists/*

# Instalar ngrok
RUN curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
    | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
    | tee /etc/apt/sources.list.d/ngrok.list && \
    apt-get update && apt-get install -y ngrok

# Configurar el authtoken de ngrok
RUN ngrok config add-authtoken 2tHm3L72AsLuKCcTGCD9Y9Ztlux_7CfAq6i4MCuj1EUAfZFST

# Cambiar de nuevo al usuario markmur88
USER markmur88

# Configurar permisos para permitir modificaciones en el directorio de trabajo
USER root
RUN mkdir -p /home/app && chown -R markmur88:markmur88 /home/app && chmod -R 775 /home/app

USER markmur88

# Configurar PostgreSQL
USER postgres
RUN /etc/init.d/postgresql start && \
    until pg_isready -U postgres; do echo "Esperando a PostgreSQL..."; sleep 2; done && \
    createdb -U postgres mydatabase && \
    psql -U postgres -c "CREATE USER markmur88 WITH PASSWORD '${markmur88cpwd}';" && \
    psql -U postgres -c "ALTER USER markmur88 WITH SUPERUSER;"

USER markmur88

WORKDIR /home/app

# Copiar archivos y configurar entorno Python
COPY . .
RUN python3 -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Exponer puertos necesarios
EXPOSE 8000

# Instalación de dependencias de Node.js y compilación de estáticos
RUN npm ci --production && npm cache clean --force && \
    npm run build

# Configuración de Django
USER root
RUN service postgresql start && \
    su - markmur88 -c "/home/app/.venv/bin/python /home/app/manage.py collectstatic --noinput && \
                       /home/app/.venv/bin/python /home/app/manage.py makemigrations && \
                       /home/app/.venv/bin/python /home/app/manage.py migrate"

# Comando por defecto para iniciar PostgreSQL, la aplicación y ngrok
USER root
CMD ["bash", "-c", "service postgresql start && su - markmur88 -c 'cd /home/app && /home/app/.venv/bin/python /home/app/manage.py runserver 0.0.0.0:8000 && ngrok http http://localhost:8000'"]