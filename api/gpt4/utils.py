import hashlib
import json
import os
import logging
from datetime import datetime
from django.conf import settings
import xml.etree.ElementTree as ET
import qrcode
import requests
import time
import random
import string
import uuid
import re

from django.contrib import messages
from requests.structures import CaseInsensitiveDict
from requests_oauthlib import OAuth2Session
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from jsonschema import validate, ValidationError

from api.gpt4.validator import preparar_request_type_y_datos
from schemas import sepa_credit_transfer_schema


logger = logging.getLogger(__name__)

# Configuramos el logger principal de transferencias
TRANSFER_LOG_DIR = os.path.join("schemas", "transferencias")
os.makedirs(TRANSFER_LOG_DIR, exist_ok=True)

SCHEMA_DIR = os.path.join("schemas", "transferencias")
os.makedirs(SCHEMA_DIR, exist_ok=True)

ZCOD_DIR = os.path.join("schemas")
os.makedirs(ZCOD_DIR, exist_ok=True)

TIMEOUT_REQUEST = 10

DEUTSCHE_BANK_CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
DEUTSCHE_BANK_CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'

ORIGIN = "https://api-bank-heroku-72c443ab11d3.herokuapp.com"

DEUTSCHE_BANK_TOKEN_URL = 'https://api.db.com:443/gw/oidc/token'
URL = "https://api.db.com:443/gw/dbapi/banking/transactions/v2"
API = "https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"

BANK_API_URL = URL

DEUTSCHE_BANK_OTP_URL = 'https://api.db.com:443/gw/dbapi/others/onetimepasswords/v2/single'

OTP_MODE = 'F'  # 'G' para OTP dinámico, 'F' para OTP fijo
OTP_URL = DEUTSCHE_BANK_OTP_URL

tokenF = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"
tokenMk = "H858hfhg0ht40588hhfjpfhhd9944940jf"
TOKEN = tokenMk

# Configura tus variables desde entorno
CLIENT_ID = DEUTSCHE_BANK_CLIENT_ID
CLIENT_SECRET = DEUTSCHE_BANK_CLIENT_SECRET
TOKEN_URL = DEUTSCHE_BANK_TOKEN_URL

def obtener_ruta_schema_transferencia(payment_id):
    # Convertir payment_id a cadena para evitar errores con UUID
    carpeta = os.path.join(SCHEMA_DIR, str(payment_id))
    os.makedirs(carpeta, exist_ok=True)
    return carpeta

# ===========================
# LOGS Y HEADERS
# ===========================

def setup_logger(payment_id):
    logger = logging.getLogger(f'transferencia_{payment_id}')
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        file_handler = logging.FileHandler(os.path.join(TRANSFER_LOG_DIR, f'transferencia_{payment_id}.log'))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

def save_log(payment_id, request_headers=None, request_body=None, response_headers=None, response_body=None):
    logger = setup_logger(payment_id)
    logger.info("=========== PETICIÓN ===========")
    if request_headers:
        logger.info(f"Headers de petición: {request_headers}")
    if request_body:
        logger.info(f"Body de petición: {request_body}")
    logger.info("=========== RESPUESTA ===========")
    if response_headers:
        logger.info(f"Headers de respuesta: {response_headers}")
    if response_body:
        logger.info(f"Body de respuesta: {response_body}")

def read_log_file(payment_id):
    log_path = os.path.join(TRANSFER_LOG_DIR, f'transferencia_{payment_id}.log')
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return None

def default_request_headers():
    return {
        "Accept": "text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "es-CO",
        "Connection": "keep-alive",
        "Host": "api.db.com",
        "Priority": "u=0, i",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
        "Origin": ORIGIN

    }

# ========================
# 9. Registro de Logs de Transferencias
# ========================

def registrar_log(payment_id, headers_enviados, response_text="", error=None, extra_info=None):
    """
    Guarda un log detallado por transferencia, incluyendo headers, respuesta y errores si aplica.
    """
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    log_path = os.path.join(carpeta, f"transferencia_{payment_id}.log")

    with open(log_path, 'a', encoding='utf-8') as log:
        log.write("\n" + "="*80 + "\n")
        log.write(f"Fecha y hora: {datetime.now()}\n")
        log.write("="*80 + "\n")
        log.write("=== Headers enviados ===\n")
        log.write(json.dumps(headers_enviados, indent=4))
        log.write("\n\n")
        if extra_info:
            log.write("=== Información adicional ===\n")
            log.write(f"{extra_info}\n\n")
        if error:
            log.write("=== Error ===\n")
            log.write(f"{error}\n")
        else:
            log.write("=== Respuesta ===\n")
            log.write(f"{response_text}\n")
        log.write("="*80 + "\n\n")
        
# ===========================
# ACCESS TOKEN
# ===========================



# Variables internas
_access_token = TOKEN
_token_expiry = 600  # 1 hora por defecto

def get_access_token():
    global _access_token, _token_expiry
    current_time = time.time()
    if _access_token and current_time < _token_expiry - 60:
        return _access_token

    data = {
        'grant_type': 'client_credentials',
        'scope': 'instant_sepa_credit_transfers'
    }
    auth = (CLIENT_ID, CLIENT_SECRET)
    try:
        response = requests.post(TOKEN_URL, data=data, auth=auth, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        _access_token = token_data['access_token']
        _token_expiry = current_time + token_data.get('expires_in', 3600)
        return _access_token
    except requests.RequestException as e:
        raise Exception(f"Error obteniendo access_token: {e}")


# ===========================
# GENERADORES DE ID
# ===========================

def generate_unique_code(length=35):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_message_id(prefix='MSG'):
    return f"{prefix}-{generate_unique_code(20)}"

def generate_instruction_id():
    return generate_unique_code(20)

def generate_end_to_end_id():
    return generate_unique_code(30)

def generate_correlation_id():
    return generate_unique_code(30)

def generate_correlation_id():
    return str(uuid.uuid4())

def generate_deterministic_id(*args, prefix=""):
    raw = ''.join(str(a) for a in args)
    hash_val = hashlib.sha256(raw.encode()).hexdigest()
    return (prefix + hash_val)[:35]

# ===========================
# OTP
# ===========================

# def get_otp_for_transfer(transfer, token):
#     headers = {
#         'Authorization': f'Bearer {token}',
#         'Content-Type': 'application/json',
#         'Correlation-Id': generate_correlation_id(),
#     }
#     body = {
#         "method": "MTAN",
#         "requestType": "INSTANT_SEPA_CREDIT_TRANSFERS",
#         "requestData": {
#             "type": "challengeRequestDataInstantSepaCreditTransfers",
#             "targetIban": transfer.creditor_account.iban,
#             "amountCurrency": transfer.currency,
#             "amountValue": float(transfer.instructed_amount)
#         },
#         "language": "es"
#     }

#     try:
#         response = requests.post(OTP_URL, json=body, headers=headers, timeout=10)
#         response.raise_for_status()
#         otp_data = response.json()
#         return otp_data['id']
#     except requests.RequestException as e:
#         raise Exception(f"Error solicitando OTP: {e}")

def get_otp_for_transfer(transfer, token):
    schema_data = transfer.to_schema_data()  # Supongamos que esta función extrae el esquema
    request_type, request_data = preparar_request_type_y_datos(schema_data)

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': generate_correlation_id(),
    }
    body = {
        "method": "MTAN",
        "requestType": request_type,
        "requestData": request_data,
        "language": "es"
    }

    try:
        response = requests.post(OTP_URL, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        otp_data = response.json()
        return otp_data['id']
    except requests.RequestException as e:
        raise Exception(f"Error solicitando OTP: {e}")


# ===========================
# ENVIO DE TRANSFERENCIAS
# ===========================

# def send_transfer(transfer, use_token=None, use_otp=None, regenerate_token=False, regenerate_otp=False):
#     payment_id = transfer.payment_id

#     token = None
#     if regenerate_token:
#         token = get_access_token()
#     else:
#         token = use_token

#     if not token:
#         raise Exception("TOKEN no disponible.")

#     otp = None
#     if regenerate_otp:
#         otp = get_otp_for_transfer(transfer, token)
#     else:
#         otp = use_otp

#     if not otp:
#         raise Exception("OTP no disponible.")

#     # (Sigue aquí construyendo el body y enviando la transferencia normalmente)

#     # Generar archivos
#     xml_path = generate_pain_001(transfer)
#     aml_path = generate_aml_file(transfer)

#     with open(xml_path, 'r', encoding='utf-8') as xml_file:
#         xml_content = xml_file.read()
#     with open(aml_path, 'r', encoding='utf-8') as aml_file:
#         aml_content = aml_file.read()
    
#     # Preparar headers
#     headers = default_request_headers()
#     headers.update({
#         'Authorization': f'Bearer {token}',
#         'Content-Type': 'application/json',
#         'idempotency-id': payment_id,
#         'otp': otp,
#     })

#     # Construir body
#     body = {
#         "purposeCode": transfer.purpose_code or "BKDF",
#         "requestedExecutionDate": transfer.requested_execution_date.strftime('%Y-%m-%d'),
#         "debtor": {
#             "debtorName": transfer.debtor.name,
#             "debtorPostalAddress": {
#                 "country": transfer.debtor.postal_address_country,
#                 "addressLine": {
#                     "streetAndHouseNumber": transfer.debtor.postal_address_street,
#                     "zipCodeAndCity": transfer.debtor.postal_address_city,
#                 }
#             }
#         },
#         "debtorAccount": {
#             "iban": transfer.debtor_account.iban,
#             "currency": transfer.debtor_account.currency,
#         },
#         "paymentIdentification": {
#             "endToEndIdentification": generate_end_to_end_id(),
#             "instructionId": generate_instruction_id(),
#         },
#         "instructedAmount": {
#             "amount": float(transfer.instructed_amount),
#             "currency": transfer.currency,
#         },
#         "creditorAgent": {
#             "financialInstitutionId": transfer.creditor_agent.financial_institution_id or "",
#         },
#         "creditor": {
#             "creditorName": transfer.creditor.name,
#             "creditorPostalAddress": {
#                 "country": transfer.creditor.postal_address_country,
#                 "addressLine": {
#                     "streetAndHouseNumber": transfer.creditor.postal_address_street,
#                     "zipCodeAndCity": transfer.creditor.postal_address_city,
#                 }
#             }
#         },
#         "creditorAccount": {
#             "iban": transfer.creditor_account.iban,
#             "currency": transfer.creditor_account.currency,
#         },
#         "remittanceInformationUnstructured": transfer.remittance_information_unstructured or "Pago de servicios",
#     }

#     # Validar contra el schema
#     try:
#         validate(instance=body, schema=sepa_credit_transfer_schema)
#     except ValidationError as e:
#         raise Exception(f"El cuerpo de la transferencia no cumple con el esquema SEPA: {e.message}")

#     # Enviar petición
#     response = requests.post(BANK_API_URL, json=body, headers=headers)

#     # Guardar en logs
#     save_log(
#         payment_id,
#         request_headers=headers,
#         request_body=body,
#         response_headers=dict(response.headers),
#         response_body=response.text
#     )

#     # Actualizar estado de la transferencia
#     if response.status_code == 201:
#         transfer.status = 'ENVIADO'
#     else:
#         transfer.status = 'ERROR'
#     transfer.save()

#     return response


def send_transfer(transfer, use_token=None, use_otp=None, regenerate_token=False, regenerate_otp=False):
    schema_data = transfer.to_schema_data()
    request_type, request_data = preparar_request_type_y_datos(schema_data)

    payment_id = transfer.payment_id

    token = None
    if regenerate_token:
        token = get_access_token()
    else:
        token = use_token

    if not token:
        raise Exception("TOKEN no disponible.")

    otp = None
    if regenerate_otp:
        otp = get_otp_for_transfer(transfer, token)
    else:
        otp = use_otp

    if not otp:
        raise Exception("OTP no disponible.")

    headers = default_request_headers()
    headers.update({
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'idempotency-id': payment_id,
        'otp': otp,
    })

    body = schema_data
    body['paymentIdentification'] = {
        "endToEndIdentification": generate_end_to_end_id(),
        "instructionId": generate_instruction_id(),
    }

    try:
        validate(instance=body, schema=sepa_credit_transfer_schema)
    except ValidationError as e:
        raise Exception(f"El cuerpo de la transferencia no cumple con el esquema SEPA: {e.message}")

    response = requests.post(BANK_API_URL, json=body, headers=headers)

    save_log(
        payment_id,
        request_headers=headers,
        request_body=body,
        response_headers=dict(response.headers),
        response_body=response.text
    )

    if response.status_code == 201:
        transfer.status = 'ENVIADO'
    else:
        transfer.status = 'ERROR'
    transfer.save()

    return response

# ===========================
# 6. Creación de PDFs de Transferencia
# ===========================

def generar_pdf_transferencia(transferencia):
    """
    Genera un PDF resumen de la transferencia SEPA.
    """
    creditor_name = transferencia.creditor.name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payment_reference = transferencia.payment_id
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_reference)

    pdf_filename = f"{creditor_name}_{timestamp}_{payment_reference}.pdf"
    pdf_path = os.path.join(carpeta_transferencia, pdf_filename)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    current_y = height - 50

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, current_y, "SEPA Transfer Receipt")
    current_y = 650

    # Tabla Cabecera
    header_data = [
        ["Creation Date", datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
        ["Payment Reference", transferencia.payment_id]
    ]
    crear_tabla_pdf(c, header_data, current_y)
    current_y -= 120

    # Tabla Deudor
    debtor_data = [
        ["Debtor Information", ""],
        ["Name", transferencia.debtor.name],
        ["IBAN", transferencia.debtor_account.iban],
        # ["Customer ID", transferencia.debtor.customer_id],
        ["Address", f"{transferencia.debtor.postal_address_country}, {transferencia.debtor.postal_address_city}, {transferencia.debtor.postal_address_street}"]
    ]
    crear_tabla_pdf(c, debtor_data, current_y)
    current_y -= 120

    # Tabla Acreedor
    creditor_data = [
        ["Creditor Information", ""],
        ["Name", transferencia.creditor.name],
        ["IBAN", transferencia.creditor_account.iban],
        ["BIC", transferencia.creditor_agent.bic],
        ["Address", f"{transferencia.creditor.postal_address_country}, {transferencia.creditor.postal_address_city}, {transferencia.creditor.postal_address_street}"]
    ]
    crear_tabla_pdf(c, creditor_data, current_y)
    current_y -= 200

    # Tabla Transferencia
    transfer_data = [
        ["Transfer Details", ""],
        ["Amount", f"{transferencia.instructed_amount} {transferencia.currency}"],
        ["Requested Execution Date", transferencia.requested_execution_date.strftime('%d/%m/%Y')],
        ["Purpose Code", transferencia.purpose_code],
        ["Remittance Info Structured", transferencia.remittance_information_structured or 'N/A'],
        ["Remittance Info Unstructured", transferencia.remittance_information_unstructured or 'N/A'],
        ["Transaction Status", transferencia.status],
        ["Priority", transferencia.payment_type_information.service_level_code],
    ]
    crear_tabla_pdf(c, transfer_data, current_y)

    # Generar QR de referencia
    c.showPage()
    qr = qrcode.make(transferencia.payment_id)
    qr_path = os.path.join(carpeta_transferencia, f"qr_{payment_reference}.png")
    qr.save(qr_path)

    qr_image = ImageReader(qr_path)
    c.drawImage(qr_image, width / 2.0 - 75, height / 2.0 - 75, width=150, height=150)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2.0, 50, "Generated automatically by SEPA Transfer System.")

    c.save()

    # Limpieza QR temporal
    if os.path.exists(qr_path):
        os.remove(qr_path)

    return pdf_path

def crear_tabla_pdf(c, data, y_position):
    """
    Crea una tabla en PDF desde una lista de listas.
    """
    table = Table(data, colWidths=[180, 350])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    table.wrapOn(c, 50, y_position)
    table.drawOn(c, 50, y_position)


