import json
import requests
from swif_transfers_api import settings
from .models import TransferenciaSWIFT
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import random
import time

SWIFT_API_URL = settings.SWIFT_API_URL  # URL de la API SWIFT
SWIFT_API_KEY = settings.SWIFT_API_KEY  # Token de autenticación

def manejar_respuesta_swift(response):
    """
    Maneja la respuesta de la API SWIFT.
    """
    try:
        response_json = response.json()
    except ValueError:
        response_json = {"error": "La API SWIFT no devolvió una respuesta válida"}
    return response_json

def imprimir_debug(headers, payload, response):
    """
    Imprime los detalles de la solicitud y la respuesta para depuración.
    """
    print("Enviando solicitud SWIFT:")
    print("Headers:", json.dumps(headers, indent=4))  # Imprime los headers
    print("Payload:", json.dumps(payload, indent=4))  # Imprime el payload
    print("Código de estado:", response.status_code)
    print("Texto de respuesta:", response.text)

def enviar_transferencia_swift(datos):
    """
    Envía una solicitud de transferencia a la API SWIFT.
    """
    payload = {
        "banco_origen": datos["banco_origen"],
        "codigo_swift_origen": datos["codigo_swift_origen"],
        "numero_cuenta_origen": datos["numero_cuenta_origen"],
        "nombre_origen": datos["nombre_origen"],
        "banco_destino": datos["banco_destino"],
        "codigo_swift_destino": datos["codigo_swift_destino"],
        "numero_cuenta_destino": datos["numero_cuenta_destino"],
        "nombre_beneficiario": datos["nombre_beneficiario"],
        "moneda": datos["moneda"],
        "monto": datos["monto"],
        "referencia": datos["referencia"]
    }
    
    headers = {
        "Authorization": f"Bearer {SWIFT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(SWIFT_API_URL, json=payload, headers=headers)
        imprimir_debug(headers, payload, response)
        response_json = manejar_respuesta_swift(response)
        
    except requests.exceptions.RequestException as e:
        response_json = {"error": "Error en la conexión con SWIFT", "detalle": str(e)}
    
    return response_json

def procesar_transferencia(referencia, monto):
    """
    Procesa una transferencia SWIFT.
    """
    transferencia = TransferenciaSWIFT.objects.get(referencia=referencia)
    datos = {
        "banco_origen": transferencia.banco_origen,
        "codigo_swift_origen": transferencia.codigo_swift_origen,
        "numero_cuenta_origen": transferencia.numero_cuenta_origen,
        "nombre_origen": transferencia.nombre_origen,
        "banco_destino": transferencia.banco_destino,
        "codigo_swift_destino": transferencia.codigo_swift_destino,
        "numero_cuenta_destino": transferencia.numero_cuenta_destino,
        "nombre_beneficiario": transferencia.nombre_beneficiario,
        "moneda": transferencia.moneda,
        "monto": monto,
        "referencia": referencia
    }
    resultado = enviar_transferencia_swift(datos)
    if "error" in resultado:
        transferencia.estado = "Fallida"
    else:
        transferencia.estado = "Completada"
    transferencia.save()
    return resultado

def simular_respuesta_swift(referencia, monto):
    """
    Simula una respuesta de la API SWIFT.
    """
    time.sleep(2)  # Simula un retraso en la transacción (como en la vida real)
    estados = ["Completada", "Fallida"]
    
    return {
        "referencia": referencia,
        "estado": random.choice(estados),  # Simula éxito o falla aleatoriamente
        "monto": monto,
        "swift_transaction_id": f"SWFT{random.randint(100000, 999999)}",
        "mensaje": "Simulación de SWIFT completada"
    }

def generar_pdf_transferencia(transferencia):
    """
    Genera un PDF con los detalles de la transacción.
    """
    # Nombre del archivo PDF
    pdf_filename = f"transferencia_{transferencia.referencia}.pdf"
    pdf_path = os.path.join("media", pdf_filename)

    # Crear el PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # Título
    c.drawString(200, 750, "Comprobante de Transferencia SWIFT")

    # Detalles de la transferencia
    detalles = [
        f"Referencia: {transferencia.referencia}",
        f"Banco Origen: {transferencia.banco_origen}",
        f"SWIFT Origen: {transferencia.codigo_swift_origen}",
        f"Cuenta Origen: {transferencia.numero_cuenta_origen}",
        f"Banco Destino: {transferencia.banco_destino}",
        f"SWIFT Destino: {transferencia.codigo_swift_destino}",
        f"Cuenta Destino: {transferencia.numero_cuenta_destino}",
        f"Beneficiario: {transferencia.nombre_beneficiario}",
        f"Monto: {transferencia.monto} {transferencia.moneda}",
        f"Estado: {transferencia.estado}",
        f"ID Transacción SWIFT: {transferencia.referencia}",
    ]
 
    y = 720
    for detalle in detalles:
        c.drawString(100, y, detalle)
        y -= 20

    c.save()
    return pdf_path