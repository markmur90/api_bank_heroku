import hashlib
import json
import os
import logging
from datetime import datetime, timezone
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
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from jsonschema import validate, ValidationError
from lxml import etree

logger = logging.getLogger(__name__)

# Configuramos el logger principal de transferencias
TRANSFER_LOG_DIR = os.path.join("schemas", "transferencias")
os.makedirs(TRANSFER_LOG_DIR, exist_ok=True)
SCHEMA_DIR = os.path.join("schemas", "transferencias")
os.makedirs(SCHEMA_DIR, exist_ok=True)
ZCOD_DIR = os.path.join("schemas")
os.makedirs(ZCOD_DIR, exist_ok=True)

TIMEOUT_REQUEST = 10

ORIGIN = "https://api-bank-heroku-72c443ab11d3.herokuapp.com"

TOKEN_URL = 'https://api.db.com:443/gw/oidc/token'
OTP_URL = 'https://api.db.com:443/gw/dbapi/others/onetimepasswords/v2/single'
AUTH_URL = 'https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges'
API_URL = "https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"

tokenF = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"
tokenMk = "H858hfhg0ht40588hhfjpfhhd9944940jf"

CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'


def obtener_ruta_schema_transferencia(payment_id):
    carpeta = os.path.join(SCHEMA_DIR, str(payment_id))
    os.makedirs(carpeta, exist_ok=True)
    return carpeta

def generar_xml_pain001(transferencia, payment_id):
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)

    # Crear el root del XML
    root = ET.Element("Document", xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03")
    cstmr_cdt_trf_initn = ET.SubElement(root, "CstmrCdtTrfInitn")

    # Cabecera del grupo
    grp_hdr = ET.SubElement(cstmr_cdt_trf_initn, "GrpHdr")
    ET.SubElement(grp_hdr, "MsgId").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(grp_hdr, "CreDtTm").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ET.SubElement(grp_hdr, "NbOfTxs").text = "1"
    ET.SubElement(grp_hdr, "CtrlSum").text = str(transferencia.instructed_amount)
    initg_pty = ET.SubElement(grp_hdr, "InitgPty")
    ET.SubElement(initg_pty, "Nm").text = transferencia.debtor.name

    # Información del pago
    pmt_inf = ET.SubElement(cstmr_cdt_trf_initn, "PmtInf")
    ET.SubElement(pmt_inf, "PmtInfId").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
    ET.SubElement(pmt_inf, "BtchBookg").text = "false"
    ET.SubElement(pmt_inf, "NbOfTxs").text = "1"
    ET.SubElement(pmt_inf, "CtrlSum").text = str(transferencia.instructed_amount)

    # Información del tipo de pago
    pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
    svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
    ET.SubElement(svc_lvl, "Cd").text = "SEPA"

    # Datos del deudor
    dbtr = ET.SubElement(pmt_inf, "Dbtr")
    ET.SubElement(dbtr, "Nm").text = transferencia.debtor.name
    dbtr_pstl_adr = ET.SubElement(dbtr, "PstlAdr")
    ET.SubElement(dbtr_pstl_adr, "StrtNm").text = transferencia.debtor.postal_address_street
    ET.SubElement(dbtr_pstl_adr, "TwnNm").text = transferencia.debtor.postal_address_city
    ET.SubElement(dbtr_pstl_adr, "Ctry").text = transferencia.debtor.postal_address_country

    dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
    dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
    ET.SubElement(dbtr_acct_id, "IBAN").text = transferencia.debtor_account.iban

    # Información de la transferencia individual
    cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
    pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
    ET.SubElement(pmt_id, "EndToEndId").text = str(transferencia.payment_identification.end_to_end_id)  # Convertir UUID a cadena
    ET.SubElement(pmt_id, "InstrId").text = str(transferencia.payment_identification.instruction_id)
    
    amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
    ET.SubElement(amt, "InstdAmt", Ccy=transferencia.currency).text = str(transferencia.instructed_amount)

    # Datos del acreedor
    cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
    ET.SubElement(cdtr, "Nm").text = transferencia.creditor.name
    cdtr_pstl_adr = ET.SubElement(cdtr, "PstlAdr")
    ET.SubElement(cdtr_pstl_adr, "StrtNm").text = transferencia.creditor.postal_address_street
    ET.SubElement(cdtr_pstl_adr, "TwnNm").text = transferencia.creditor.postal_address_city
    ET.SubElement(cdtr_pstl_adr, "Ctry").text = transferencia.creditor.postal_address_country

    cdtr_acct = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
    cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
    ET.SubElement(cdtr_acct_id, "IBAN").text = transferencia.creditor_account.iban

    # Agente del acreedor
    cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
    fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
    ET.SubElement(fin_instn_id, "BIC").text = transferencia.creditor_agent.bic

    # Información de la remesa
    rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
    if transferencia.remittance_information_structured:
        ET.SubElement(rmt_inf, "Strd").text = transferencia.remittance_information_structured
    if transferencia.remittance_information_unstructured:
        ET.SubElement(rmt_inf, "Ustrd").text = transferencia.remittance_information_unstructured

    # Guardar XML
    xml_filename = f"pain001_{payment_id}.xml"
    xml_path = os.path.join(carpeta_transferencia, xml_filename)
    ET.ElementTree(root).write(xml_path, encoding='utf-8', xml_declaration=True)

    logger.info(f"XML pain.001 generado en {xml_path}")
    return xml_path

def validar_xml_pain001(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = {'ns': "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"}
    e2e = root.find('.//ns:EndToEndId', ns)
    instr = root.find('.//ns:InstrId', ns)
    if e2e is None or not e2e.text.strip():
        raise ValueError("El XML no contiene un EndToEndId válido.")
    if instr is None or not instr.text.strip():
        raise ValueError("El XML no contiene un InstructionId válido.")

def validar_xml_con_xsd(xml_path, xsd_path="schemas/xsd/pain.001.001.03.xsd"):
    with open(xsd_path, 'rb') as f:
        schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)
    with open(xml_path, 'rb') as f:
        xml_doc = etree.parse(f)
    if not schema.validate(xml_doc):
        errors = schema.error_log
        raise ValueError(f"El XML no es válido según el XSD: {errors}")
    
def generar_archivo_aml(transferencia, payment_id):
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
    aml_filename = f"aml_{payment_id}.xml"
    aml_path = os.path.join(carpeta_transferencia, aml_filename)

    root = ET.Element("AMLTransactionReport")
    transaction = ET.SubElement(root, "Transaction")

    ET.SubElement(transaction, "TransactionID").text = str(transferencia.payment_id)  # Convertir UUID a cadena
    ET.SubElement(transaction, "TransactionType").text = "SEPA" # type: ignore

    ET.SubElement(transaction, "ExecutionDate").text = transferencia.requested_execution_date.strftime("%Y-%m-%dT%H:%M:%S")

    amount = ET.SubElement(transaction, "Amount")
    amount.set("currency", transferencia.currency)
    amount.text = str(transferencia.instructed_amount)

    debtor = ET.SubElement(transaction, "Debtor")
    ET.SubElement(debtor, "Name").text = transferencia.debtor.name
    ET.SubElement(debtor, "IBAN").text = transferencia.debtor_account.iban
    ET.SubElement(debtor, "Country").text = transferencia.debtor.postal_address_country
    ET.SubElement(debtor, "CustomerID").text = transferencia.debtor.customer_id
    ET.SubElement(debtor, "KYCVerified").text = "true"

    creditor = ET.SubElement(transaction, "Creditor")
    ET.SubElement(creditor, "Name").text = transferencia.creditor.name
    ET.SubElement(creditor, "IBAN").text = transferencia.creditor_account.iban
    ET.SubElement(creditor, "BIC").text = transferencia.creditor_agent.financial_institution_id
    ET.SubElement(creditor, "Country").text = transferencia.creditor.postal_address_country

    ET.SubElement(transaction, "Purpose").text = transferencia.purpose_code or "N/A"
    ET.SubElement(transaction, "Channel").text = "Online"
    ET.SubElement(transaction, "RiskScore").text = "3"
    ET.SubElement(transaction, "PEP").text = "false"
    ET.SubElement(transaction, "SanctionsCheck").text = "clear"
    ET.SubElement(transaction, "HighRiskCountry").text = "false"

    flags = ET.SubElement(transaction, "Flags")
    ET.SubElement(flags, "UnusualAmount").text = "false"
    ET.SubElement(flags, "FrequentTransfers").text = "false"
    ET.SubElement(flags, "ManualReviewRequired").text = "false"

    ET.ElementTree(root).write(aml_path, encoding="utf-8", xml_declaration=True)
    return aml_path

def validar_aml_con_xsd(aml_path, xsd_path="schemas/xsd/aml_transaction_report.xsd"):
    """
    Valida el archivo AML generado contra su esquema XSD.
    """
    with open(xsd_path, 'rb') as f:
        schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)

    with open(aml_path, 'rb') as f:
        xml_doc = etree.parse(f)

    if not schema.validate(xml_doc):
        errors = schema.error_log
        raise ValueError(f"El archivo AML no es válido según el XSD: {errors}")

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

def registrar_log(payment_id, headers_enviados, response_text="", error=None, extra_info=None):
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

def read_log_file(payment_id):
    log_path = os.path.join(TRANSFER_LOG_DIR, f'transferencia_{payment_id}.log')
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        return None

def handle_error_response(response):
    errores = {
        2: "Valor inválido para uno de los parámetros.",
        16: "Respuesta de desafío OTP inválida.",
        17: "OTP inválido.",
        114: "No se pudo identificar la transacción por Id.",
        127: "La fecha de reserva inicial debe preceder a la fecha de reserva final.",
        131: "Valor inválido para 'sortBy'. Valores válidos: 'bookingDate[ASC]' y 'bookingDate[DESC]'.",
        132: "No soportado.",
        138: "Parece que inició un desafío no pushTAN. Use el endpoint PATCH para continuar.",
        139: "Parece que inició un desafío pushTAN. Use el endpoint GET para continuar.",
        6500: "Parámetros en la URL o tipo de contenido incorrectos. Por favor, revise y reintente.",
        6501: "Detalles del banco contratante inválidos o faltantes.",
        6502: "La moneda aceptada para el monto instruido es EUR. Por favor, corrija su entrada.",
        6503: "Parámetros enviados son inválidos o faltantes.",
        6504: "Los parámetros en la solicitud no coinciden con la solicitud inicial.",
        6505: "Fecha de ejecución inválida.",
        6506: "El IdempotencyId ya está en uso.",
        6507: "No se permite la cancelación para esta transacción.",
        6508: "Pago SEPA no encontrado.",
        6509: "El parámetro en la solicitud no coincide con el último Auth id.",
        6510: "El estado actual no permite la actualización del segundo factor con la acción proporcionada.",
        6511: "Fecha de ejecución inválida.",
        6515: "El IBAN de origen o el tipo de cuenta son inválidos.",
        6516: "No se permite la cancelación para esta transacción.",
        6517: "La moneda aceptada para la cuenta del acreedor es EUR. Por favor, corrija su entrada.",
        6518: "La fecha de recolección solicitada no debe ser un día festivo o fin de semana. Por favor, intente nuevamente.",
        6519: "La fecha de ejecución solicitada no debe ser mayor a 90 días en el futuro. Por favor, intente nuevamente.",
        6520: "El valor de 'requestedExecutionDate' debe coincidir con el formato yyyy-MM-dd.",
        6521: "La moneda aceptada para la cuenta del deudor es EUR. Por favor, corrija su entrada.",
        6523: "No hay una entidad legal presente para el IBAN de origen. Por favor, corrija su entrada.",
        6524: "Ha alcanzado el límite máximo permitido para el día. Espere hasta mañana o reduzca el monto de la transferencia.",
        6525: "Por el momento, no soportamos photo-tan para pagos masivos.",
        6526: "El valor de 'createDateTime' debe coincidir con el formato yyyy-MM-dd'T'HH:mm:ss.",
        401: "La función solicitada requiere un nivel de autenticación SCA.",
        404: "No se encontró el recurso solicitado.",
        409: "Conflicto: El recurso ya existe o no se puede procesar la solicitud."
    }
    try:
        data = response.json()
        code = data.get('code') or data.get('errorCode')
        if code is not None:
            try:
                code_int = int(code)
                if code_int in errores:
                    return errores[code_int]
            except (ValueError, TypeError):
                pass
        if isinstance(data, dict) and 'message' in data:
            return data.get('message')
        if isinstance(data, list):
            return "; ".join(item.get('message', str(item)) for item in data)
        return response.text
    except ValueError:
        return response.text

def default_request_headers():
    return {
        "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
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
        "Origin": ORIGIN,
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        'x-request-Id': str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest", 
    }

# ===========================
# ACCESS TOKEN
# ===========================
# Variables internas
_access_token = None
_token_expiry = 3600  # 1 hora por defecto
def get_access_token():
    global _access_token, _token_expiry
    current_time = time.time()
    if _access_token and current_time < _token_expiry - 60:
        return _access_token

    data = {
        'grant_type': 'client_credentials',
        'scope': 'sepa_credit_transfers'
    }
    auth = (CLIENT_ID, CLIENT_SECRET)
    try:
        response = requests.post(TOKEN_URL, data=data, auth=auth, timeout=10)

        token_data = response.json()
        _access_token = token_data['access_token']
        _token_expiry = current_time + token_data.get('expires_in', 3600)
        return _access_token
    except requests.RequestException as e:
        raise Exception(f"Error obteniendo access_token: {e}")

# ===========================
# OTP
# ===========================
def preparar_request_type_y_datos(schema_data):
    request_type = "SEPA_TRANSFER_GRANT"
    datos = {
        "type": "challengeRequestDataSepaPaymentTransfer",
        "targetIban": schema_data["creditorAccount"]["iban"],
        "amountCurrency": schema_data["instructedAmount"]["currency"],
        "amountValue": schema_data["instructedAmount"]["amount"]
    }
    return request_type, datos


def crear_challenge_autorizacion1(transfer, token, payment_id):
    schema_data = transfer.to_schema_data()
    request_type, request_data = preparar_request_type_y_datos(schema_data)
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': str(payment_id),
    }
    payload = {
        "method": "PUSHTAN",
        "requestType": request_type,
        "requestData": request_data,
        "language": "de"
    }
    try:
        response = requests.post(f"{AUTH_URL}",headers=headers,json=payload,timeout=10)
        if response.status_code != 201:
            error_msg = handle_error_response(response)
            registrar_log(transfer.payment_id, headers, response.text, error=error_msg)
            raise Exception(error_msg)
        return response.json()["id"]
    except requests.RequestException as e:
        registrar_log(transfer.payment_id, headers, error=str(e))
        raise Exception(f"Error de conexión al crear challenge: {e}")

def crear_challenge_autorizacion(transfer, token, payment_id):
    schema_data = transfer.to_schema_data()
    request_type = "SEPA_TRANSFER_GRANT"
    request_data = {
        "type": "challengeRequestDataSepaPaymentTransfer",
        "targetIban": schema_data["creditorAccount"]["iban"],
        "amountCurrency": schema_data["instructedAmount"]["currency"],
        "amountValue": schema_data["instructedAmount"]["amount"]
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': str(payment_id)
    }
    payload = {
        'method': 'PUSHTAN',
        'requestType': request_type,
        'requestData': request_data,
        'language': 'de'
    }
    response = requests.post(AUTH_URL, headers=headers, json=payload, timeout=10)
    if response.status_code != 201:
        error_msg = handle_error_response(response)
        registrar_log(payment_id, headers, response.text, error=error_msg)
        raise Exception(error_msg)
    return response.json()['id']

def resolver_challenge1(challenge_id, token, payment_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': str(payment_id),
    }
    timeout_secs = 5 * 60
    start = time.time()
    while True:
        resp = requests.get(f"{AUTH_URL}/{challenge_id}", headers=headers, timeout=10)
        if resp.status_code != 200:
            error_msg = handle_error_response(resp)
            registrar_log(payment_id, headers, resp.text, error=error_msg)
            raise Exception(f"Error obteniendo estado del challenge: {error_msg}")
        data = resp.json()
        status = data.get("status")
        if status == "VALIDATED":
            return data["challengeProofToken"]
        elif status == "PENDING":
            if time.time() - start > timeout_secs:
                msg = "Timeout agotado esperando VALIDATED"
                registrar_log(payment_id, headers, error=msg)
                raise TimeoutError(msg)
            time.sleep(1)
            continue
        elif status == "EXPIRED":
            msg = "El challenge ha expirado (status=EXPIRED)"
            registrar_log(payment_id, headers, resp.text, error=msg)
            raise Exception(msg)
        elif status == "REJECTED":
            msg = "El challenge fue rechazado por el usuario (status=REJECTED)"
            registrar_log(payment_id, headers, resp.text, error=msg)
            raise Exception(msg)
        elif status == "EIDP_ERROR":
            msg = "Error interno de EIDP procesando el challenge (status=EIDP_ERROR)"
            registrar_log(payment_id, headers, resp.text, error=msg)
            raise Exception(msg)
        else:
            msg = f"Estado de challenge desconocido: {status}"
            registrar_log(payment_id, headers, resp.text, error=msg)
            raise Exception(msg)

def resolver_challenge(challenge_id, token, payment_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Correlation-Id': str(payment_id)
    }
    start = time.time()
    while True:
        response = requests.get(f"{AUTH_URL}/{challenge_id}", headers=headers, timeout=10)
        data = response.json()
        status = data.get('status')
        if status == 'VALIDATED':
            return data['challengeProofToken']
        if status == 'PENDING' and time.time() - start < 300:
            msg = "Timeout agotado esperando VALIDATED"
            registrar_log(payment_id, headers, error=msg)
            raise TimeoutError(msg)
            time.sleep(1)
            continue
        elif status == "EXPIRED":
            msg = "El challenge ha expirado (status=EXPIRED)"
            registrar_log(payment_id, headers, response.text, error=msg)
            raise Exception(msg)
        elif status == "REJECTED":
            msg = "El challenge fue rechazado por el usuario (status=REJECTED)"
            registrar_log(payment_id, headers, response.text, error=msg)
            raise Exception(msg)
        elif status == "EIDP_ERROR":
            msg = "Error interno de EIDP procesando el challenge (status=EIDP_ERROR)"
            registrar_log(payment_id, headers, response.text, error=msg)
            raise Exception(msg)
        else:
            msg = f"Estado de challenge desconocido: {status}"
            registrar_log(payment_id, headers, response.text, error=msg)
            raise Exception(msg)
  
def obtener_otp_automatico_con_challenge(transfer):
    token = get_access_token()
    challenge_id = crear_challenge_autorizacion(transfer, token, transfer.payment_id)
    otp_token = resolver_challenge(challenge_id, token, transfer.payment_id)
    return otp_token, token

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

def generate_deterministic_id(*args, prefix=""):
    raw = ''.join(str(a) for a in args)
    hash_val = hashlib.sha256(raw.encode()).hexdigest()
    return (prefix + hash_val)[:35]

def generate_payment_id_uuid() -> str:
    return uuid.uuid4()

def send_transfer1(transfer, use_token=None, use_otp=None, regenerate_token=False, regenerate_otp=False):
    schema_data = transfer.to_schema_data()
    payment_id = str(transfer.payment_id)
    token = None
    if regenerate_token:
        token = get_access_token()
    else:
        token = use_token
    if not token:
        raise Exception("TOKEN no disponible.")
    otp = None
    if regenerate_otp:
        otp = obtener_otp_automatico_con_challenge(transfer, token)
    else:
        otp = use_otp
    if not otp:
        raise Exception("OTP no disponible.")
    headers = default_request_headers()
    headers.update({
        'Authorization': f'Bearer {token}',
        
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'idempotency-id': str(payment_id),
        'Correlation-Id': str(payment_id),
        'x-request-Id': str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest", 

        'otp': otp,
    })
    body = schema_data
    response = requests.post(API_URL, json=body, headers=headers)
    registrar_log(
        payment_id,
        request_headers=headers,
        request_body=body,
        response_headers=dict(response.headers),
        response_body=response.text
    )
    if response.status_code == 201:
        transfer.status = 'PNDG'
    else:
        transfer.status = 'RJCT'
    transfer.save()
    try:
        generar_xml_pain001(transfer, payment_id)
        generar_archivo_aml(transfer, payment_id, instant_transfer=transfer._instant_transfer_flag)
        aml_path = generar_archivo_aml(transfer, payment_id, instant_transfer=transfer._instant_transfer_flag)
        xml_path = generar_xml_pain001(transfer, payment_id)
        validar_xml_pain001(xml_path)
        validar_xml_con_xsd(xml_path)
        validar_aml_con_xsd(aml_path)
        logger = setup_logger(payment_id)
        logger.info("Validación de XML pain.001 superada correctamente.")
    except Exception as e:
        registrar_log(payment_id, response_body=f"Error generando XML posterior: {str(e)}")
    return response


def send_transfer(transfer, use_token=None, use_otp=None, regenerate_token=False, regenerate_otp=False):
    schema_data = transfer.to_schema_data()
    token = get_access_token() if regenerate_token or not use_token else use_token
    proof_token, token = obtener_otp_automatico_con_challenge(transfer) if regenerate_otp or not use_otp else (use_otp, token)
    headers = default_request_headers()
    headers.update({
        'Authorization': f'Bearer {token}',
        'idempotency-id': str(transfer.payment_id),
        'Correlation-Id': str(transfer.payment_id),
        'X-DBAPI-Challenge-Proof-Token': proof_token
    })
    response = requests.post(API_URL, json=schema_data, headers=headers)
    registrar_log(
        transfer.payment_id,
        request_headers=headers,
        request_body=schema_data,
        response_headers=dict(response.headers),
        response_body=response.text
    )
    transfer.status = 'PDNG' if response.status_code == 201 else 'RJCT'
    transfer.save()
    try:
        generar_xml_pain001(transfer.payment_id)
        generar_archivo_aml(transfer.payment_id)
        aml_path = generar_archivo_aml(transfer.payment_id)
        xml_path = generar_xml_pain001(transfer.payment_id)
        validar_xml_pain001(xml_path)
        validar_xml_con_xsd(xml_path)
        validar_aml_con_xsd(aml_path)
        logger = setup_logger(transfer.payment_id)
        logger.info("Validación de XML pain.001 superada correctamente.")
    except Exception as e:
        registrar_log(transfer.payment_id, response_body=f"Error generando XML posterior: {str(e)}")    
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



