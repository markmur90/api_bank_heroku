from flask import Flask, request, Response
import requests
import csv
import os
from datetime import datetime

app = Flask(__name__)
TARGET_API = 'https://api-bank-heroku-72c443ab11d3.herokuapp.com'
LOG_FILE = 'honeypot_h_logs.csv'

def write_log(data):
    existe = os.path.exists(LOG_FILE)
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(data.keys()))
        if not existe:
            writer.writeheader()
        writer.writerow(data)

@app.route('/admin', methods=['GET','POST','PUT','DELETE','PATCH'])
def honeypot():
    info = {
        'ip': request.remote_addr,
        'path': request.path,
        'method': request.method,
        'headers': dict(request.headers),
        'params': request.args.to_dict(),
        'body': request.get_data().decode('utf-8', 'ignore'),
        'timestamp': datetime.utcnow().isoformat()
    }
    write_log(info)
    return Response('Not Found', status=404)

@app.route('/<path:path>', methods=['GET','POST','PUT','DELETE','PATCH'])
def proxy(path):
    destino = f"{TARGET_API}/{path}"
    resp = requests.request(
        method=request.method,
        url=destino,
        headers={k:v for k,v in request.headers.items() if k.lower()!='host'},
        params=request.args,
        data=request.get_data(),
        allow_redirects=False
    )
    excluidas = ['content-encoding','content-length','transfer-encoding','connection']
    cabeceras = [(n,v) for n,v in resp.raw.headers.items() if n.lower() not in excluidas]
    return Response(resp.content, resp.status_code, cabeceras)

@app.route('/', methods=['GET'])
def mostrar_logs():
    if not os.path.exists(LOG_FILE):
        return '<h2>No hay intentos registrados aún.</h2>', 200
    with open(LOG_FILE, newline='') as f:
        lector = csv.DictReader(f)
        filas = list(lector)
    if not filas:
        return '<h2>No hay intentos registrados aún.</h2>', 200
    columnas = lector.fieldnames
    tabla = '<table border="1" cellpadding="5"><tr>' + ''.join(f'<th>{col}</th>' for col in columnas) + '</tr>'
    for fila in filas:
        tabla += '<tr>' + ''.join(f'<td>{fila[col]}</td>' for col in columnas) + '</tr>'
    tabla += '</table>'
    return tabla, 200

if __name__ == '__main__':
    port = 5001
    app.run(host='0.0.0.0', port=port)
