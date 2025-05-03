import socket
import threading
import csv
import os
import datetime

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
            # Asumimos que el cliente envía usuario:contraseña en texto plano como honeypots sencillos
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
        print(f"[*] Conexión entrante de {address[0]}:{address[1]}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
        client_thread.start()

if __name__ == "__main__":
    try:
        start_honeypot(HONEYPOT_IP, HONEYPOT_PORT)
    except KeyboardInterrupt:
        print("\n[!] Honeypot detenido manualmente.")
    except Exception as e:
        print(f"[!] Error crítico: {e}")
