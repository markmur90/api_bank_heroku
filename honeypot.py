from hashlib import new
import socket
import threading
import csv
import os
import datetime
import subprocess
from flask import Flask, render_template_string

HONEYPOT_IP="0.0.0.0"
HONEYPOT_PORT=2222
LOG_FILE="honeypot_logs.csv"
BANNER=b"SSH-2.0-OpenSSH_7.9p1 Debian-10+deb10u2\r\n"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE,mode='w',newline='') as f:
        csv.writer(f).writerow(["timestamp","ip","user_attempt","password_attempt"])

def log_attempt(ip,user,password):
    with open(LOG_FILE,mode='a',newline='') as f:
        csv.writer(f).writerow([datetime.datetime.now().isoformat(),ip,user,password])

def handle_client(client_socket,address):
    try:
        client_socket.sendall(BANNER)
        data=client_socket.recv(1024)
        if data:
            creds=data.decode(errors='ignore').strip()
            if ':' in creds:
                u,p=creds.split(':',1)
                log_attempt(address[0],u,p)
            else:
                log_attempt(address[0],creds,"(no-password)")
    finally:
        client_socket.close()

def start_honeypot():
    s=socket.socket()
    s.bind((HONEYPOT_IP,HONEYPOT_PORT))
    s.listen(100)
    while True:
        c,a=s.accept()
        threading.Thread(target=handle_client,args=(c,a)).start()

def start_dashboard():
    app=Flask(__name__)
    @app.route('/')
    def dash():
        logs=[]
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE,newline='') as f:
                logs=list(csv.DictReader(f))
        return render_template_string("""<!DOCTYPE html><html><head><title>Honeypot</title><style>body{font-family:Arial;padding:20px;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #ccc;padding:8px;}th{background:#f2f2f2;}</style></head><body><h1>Intentos SSH</h1><table><thead><tr><th>Timestamp</th><th>IP</th><th>Usuario</th><th>Contraseña</th></tr></thead><tbody>{% for l in logs %}<tr><td>{{l.timestamp}}</td><td>{{l.ip}}</td><td>{{l.user_attempt}}</td><td>{{l.password_attempt}}</td></tr>{% endfor %}</tbody></table></body></html>""",logs=logs)
    threading.Thread(target=start_honeypot,daemon=True).start()
    app.run(host='0.0.0.0',port=5000)

def free_port(port):
    subprocess.run(f"lsof -ti:{port} | xargs -r kill -9", shell=True)

free_port(HONEYPOT_PORT)
free_port(5000)
start_dashboard()
