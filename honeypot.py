import socket
import threading
import csv
import os
import subprocess
from datetime import datetime
from flask import Flask, render_template_string

HONEYPOT_IP="0.0.0.0"
HONEYPOT_PORTS=[2222,8000]
REAL_BACKEND="127.0.0.1"
GUNICORN_PORT=8001
LOG_FILE="honeypot_logs.csv"
BANNER=b"SSH-2.0-OpenSSH_7.9p1 Debian-10+deb10u2\r\n"
log_lock=threading.Lock()

def init_log_file():
    with open(LOG_FILE,mode='w',newline='') as f:
        csv.writer(f).writerow(["timestamp","ip","port","protocol","info"])

def log_attempt(ip,port,protocol,info):
    timestamp=datetime.now().isoformat()
    with log_lock,open(LOG_FILE,mode='a',newline='') as f:
        csv.writer(f).writerow([timestamp,ip,port,protocol,info])

def pipe(src,dst):
    try:
        while True:
            data=src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        try:
            dst.close()
        except:
            pass

def handle_client(client,address,port):
    if port==2222:
        try:
            client.sendall(BANNER)
            data=client.recv(1024)
            if data:
                creds=data.decode(errors='ignore').strip()
                log_attempt(address[0],port,"SSH",creds)
        finally:
            client.close()
    elif port==8000:
        remote=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            remote.connect((REAL_BACKEND,GUNICORN_PORT))
            request=client.recv(4096)
            if request:
                first_line=request.decode(errors='ignore').splitlines()[0]
                log_attempt(address[0],port,"HTTP",first_line)
                remote.sendall(request)
                remote.shutdown(socket.SHUT_WR)
                while True:
                    chunk=remote.recv(4096)
                    if not chunk:
                        break
                    client.sendall(chunk)
        except:
            pass
        finally:
            client.close()
            remote.close()

def start_honeypot(port):
    server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server.bind((HONEYPOT_IP,port))
    server.listen(1000)
    while True:
        client,addr=server.accept()
        threading.Thread(target=handle_client,args=(client,addr,port),daemon=True).start()

def start_dashboard():
    app=Flask(__name__)
    @app.route("/")
    def dashboard():
        logs=[]
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE,newline="") as f:
                logs=list(csv.DictReader(f))
        logs.sort(key=lambda l: l['timestamp'], reverse=True)
        return render_template_string(
            """<html>
<head>
<meta http-equiv="refresh" content="5">
<title>Honeypot</title>
<style>
  body{font-family:Arial;padding:20px;}
  table{width:100%;border-collapse:collapse;}
  th,td{border:1px solid #ccc;padding:8px;}
  th{background:#f2f2f2;}
</style>
</head>
<body>
<h1>Registro de intentos</h1>
<table>
  <thead>
    <tr><th>Fecha</th><th>IP</th><th>Puerto</th><th>Protocolo</th><th>Info</th></tr>
  </thead>
  <tbody>
    {% for l in logs %}
      <tr>
        <td>{{ l.timestamp }}</td>
        <td>{{ l.ip }}</td>
        <td>{{ l.port }}</td>
        <td>{{ l.protocol }}</td>
        <td>{{ l.info }}</td>
      </tr>
    {% endfor %}
  </tbody>
</table>
</body>
</html>""",
            logs=logs
        )
    app.run(host="0.0.0.0",port=5000,debug=False,threaded=True,use_reloader=False)

def free_port(port):
    subprocess.run(f"lsof -ti:{port} | xargs -r kill -9",shell=True)

def main():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    init_log_file()
    for port in HONEYPOT_PORTS:
        free_port(port)
        threading.Thread(target=start_honeypot,args=(port,),daemon=True).start()
    free_port(5000)
    start_dashboard()

if __name__=="__main__":
    main()
