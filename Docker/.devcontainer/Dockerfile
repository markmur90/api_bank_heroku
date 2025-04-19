FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

ENV PYTHONUNBUFFERED 1

# Instala dependencias necesarias
RUN apt-get update && apt-get install -y \
    postgresql postgresql-contrib \
    curl build-essential \
    && apt-get clean

# # Configura PostgreSQL
# USER postgres
# RUN /etc/init.d/postgresql start && \
#     sleep 5 && \
#     psql -c "ALTER USER postgres PASSWORD 'Ptf8454Jd55';" && \
#     createdb -U postgres swiftapi3

# # Cambia de nuevo al usuario root
# USER root

# # Configura el directorio de trabajo
# WORKDIR /workspaces

# # Copia el código de la aplicación
# COPY . .

# # Expone el puerto de PostgreSQL (5432) y cualquier otro necesario
# EXPOSE 5432

# # Comando por defecto para iniciar PostgreSQL y la aplicación
# CMD service postgresql start && sleep infinity