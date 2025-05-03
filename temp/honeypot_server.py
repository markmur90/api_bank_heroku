from hashlib import new
import socket
import threading
import csv
import os
import datetime
from webbrowser import Mozilla
from flask import Flask, render_template_string

# Configuraciones iniciales
HONEYPOT_IP = "0.0.0.0"
HONEYPOT_PORT = 2222
LOG_FILE = "honeypot_logs.csv"
BANNER = b"SSH-2.0-OpenSSH_7.9p1 Debian-10+deb10u2\r\n"

# Asegurar que existe el archivo de log con encabezado
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "ip", "user_attempt", "password_attempt"])

def log_attempt(ip, username, password):
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, ip, username, password])
    print(f"[!] Intento registrado: {ip} -> {username}:{password}")

def handle_client(client_socket, address):
    try:
        client_socket.sendall(BANNER)
        data = client_socket.recv(1024)
        if data:
            credentials = data.decode(errors='ignore').strip()
            if ':' in credentials:
                username, password = credentials.split(':', 1)
                log_attempt(address[0], username, password)
            else:
                log_attempt(address[0], credentials, "(no-password)")
    except Exception as e:
        print(f"[!] Error manejando conexión: {e}")
    finally:
        client_socket.close()

def start_honeypot(ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(100)
    print(f"[*] Honeypot SSH escuchando en {ip}:{port}")
    while True:
        client_socket, address = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
        client_thread.start()

def start_dashboard():
    app = Flask(__name__)

    @app.route('/')
    def dashboard():
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                logs = list(reader)
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Honeypot Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Intentos Capturados en Honeypot SSH</h1>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>IP</th>
                        <th>Usuario</th>
                        <th>Contraseña</th>
                    </tr>
                </thead>
                <tbody>
                {% for log in logs %}
                    <tr>
                        <td>{{ log.timestamp }}</td>
                        <td>{{ log.ip }}</td>
                        <td>{{ log.user_attempt }}</td>
                        <td>{{ log.password_attempt }}</td>
                    </tr>
                {% endfor %}
                </tbody>
            </table>
        </body>
        </html>
        """, logs=logs)

    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    try:
        threading.Thread(target=start_honeypot, args=(HONEYPOT_IP, HONEYPOT_PORT), daemon=True).start()
        start_dashboard()
    except KeyboardInterrupt:
        print("\n[!] Honeypot detenido manualmente.")
    except Exception as e:
        print(f"[!] Error crítico: {e}")
