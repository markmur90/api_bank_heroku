import os
import logging
from datetime import datetime
from django.conf import settings
import xml.etree.ElementTree as ET
import requests
import time
import random
import string
import uuid

# Configuramos el logger principal de transferencias
TRANSFER_LOG_DIR = os.path.join(settings.BASE_DIR, 'logs', 'transferencias')
os.makedirs(TRANSFER_LOG_DIR, exist_ok=True)
SCHEMA_DIR = os.path.join(settings.BASE_DIR, 'schemas')
os.makedirs(SCHEMA_DIR, exist_ok=True)

DEUTSCHE_BANK_CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
DEUTSCHE_BANK_CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'

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
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    }


# ===========================
# ACCESS TOKEN
# ===========================

# Configura tus variables desde entorno
CLIENT_ID = DEUTSCHE_BANK_CLIENT_ID
CLIENT_SECRET = DEUTSCHE_BANK_CLIENT_SECRET
TOKEN_URL = DEUTSCHE_BANK_TOKEN_URL

# Variables internas
_access_token = None
_token_expiry = 0  # epoch timestamp

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
    retries = 3
    while retries > 0:
        try:
            response = requests.post(TOKEN_URL, data=data, auth=auth, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                _access_token = token_data['access_token']
                _token_expiry = current_time + token_data.get('expires_in', 3600)
                return _access_token
            else:
                print(f"Error autenticando: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"Error en la conexión: {e}")
        retries -= 1
        time.sleep(2)
    raise Exception("Error: No se pudo obtener el token después de varios intentos.")

tokenG = get_access_token()


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


# ===========================
# OTP
# ===========================

def get_otp_for_transfer(transfer):
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
        'Correlation-Id': generate_correlation_id(),
    }
    body = {
        "method": "MTAN",
        "requestType": "INSTANT_SEPA_CREDIT_TRANSFERS",
        "requestData": {
            "type": "challengeRequestDataInstantSepaCreditTransfers",
            "targetIban": transfer.creditor_account.iban,
            "amountCurrency": transfer.currency,
            "amountValue": float(transfer.instructed_amount)
        },
        "language": "es"
    }
    retries = 3
    while retries > 0:
        try:
            response = requests.post(OTP_URL, json=body, headers=headers, timeout=10)
            if response.status_code == 201:
                otp_data = response.json()
                return otp_data['id']  # ID del desafío generado
            else:
                print(f"Error solicitando OTP: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"Error en conexión al solicitar OTP: {e}")
        retries -= 1
        time.sleep(2)
    raise Exception("Error: No se pudo obtener OTP después de varios intentos.")


# ===========================
# GENERADORES DE ARCHIVOS XML
# ===========================

def generate_pain_001(transfer):
    ns = 'urn:iso:std:iso:20022:tech:xsd:pain.001.001.03'
    ET.register_namespace('', ns)

    document = ET.Element('{%s}Document' % ns)
    cstmrCdtTrfInitn = ET.SubElement(document, '{%s}CstmrCdtTrfInitn' % ns)

    # Group Header
    grpHdr = ET.SubElement(cstmrCdtTrfInitn, '{%s}GrpHdr' % ns)
    ET.SubElement(grpHdr, '{%s}MsgId' % ns).text = generate_message_id('SEPA')
    ET.SubElement(grpHdr, '{%s}NbOfTxs' % ns).text = '1'
    ET.SubElement(grpHdr, '{%s}CtrlSum' % ns).text = str(transfer.instructed_amount)

    initgPty = ET.SubElement(grpHdr, '{%s}InitgPty' % ns)
    ET.SubElement(initgPty, '{%s}Nm' % ns).text = transfer.debtor.name

    # Payment Information
    pmtInf = ET.SubElement(cstmrCdtTrfInitn, '{%s}PmtInf' % ns)
    ET.SubElement(pmtInf, '{%s}PmtInfId' % ns).text = generate_instruction_id()
    ET.SubElement(pmtInf, '{%s}PmtMtd' % ns).text = 'TRF'
    ET.SubElement(pmtInf, '{%s}BtchBookg' % ns).text = 'false'
    ET.SubElement(pmtInf, '{%s}NbOfTxs' % ns).text = '1'
    ET.SubElement(pmtInf, '{%s}CtrlSum' % ns).text = str(transfer.instructed_amount)

    pmtTpInf = ET.SubElement(pmtInf, '{%s}PmtTpInf' % ns)
    svcLvl = ET.SubElement(pmtTpInf, '{%s}SvcLvl' % ns)
    ET.SubElement(svcLvl, '{%s}Cd' % ns).text = 'SEPA'

    ET.SubElement(pmtInf, '{%s}ReqdExctnDt' % ns).text = transfer.requested_execution_date.isoformat()

    dbtr = ET.SubElement(pmtInf, '{%s}Dbtr' % ns)
    ET.SubElement(dbtr, '{%s}Nm' % ns).text = transfer.debtor.name

    dbtrAcct = ET.SubElement(pmtInf, '{%s}DbtrAcct' % ns)
    id_dbtrAcct = ET.SubElement(dbtrAcct, '{%s}Id' % ns)
    ET.SubElement(id_dbtrAcct, '{%s}IBAN' % ns).text = transfer.debtor_account.iban

    dbtrAgt = ET.SubElement(pmtInf, '{%s}DbtrAgt' % ns)
    finInstnId = ET.SubElement(dbtrAgt, '{%s}FinInstnId' % ns)
    if transfer.creditor_agent.bic:
        ET.SubElement(finInstnId, '{%s}BIC' % ns).text = transfer.creditor_agent.bic

    chrgBr = ET.SubElement(pmtInf, '{%s}ChrgBr' % ns)
    chrgBr.text = 'SLEV'

    cdtTrfTxInf = ET.SubElement(pmtInf, '{%s}CdtTrfTxInf' % ns)
    pmtId = ET.SubElement(cdtTrfTxInf, '{%s}PmtId' % ns)
    ET.SubElement(pmtId, '{%s}EndToEndId' % ns).text = generate_end_to_end_id()

    amt = ET.SubElement(cdtTrfTxInf, '{%s}Amt' % ns)
    instdAmt = ET.SubElement(amt, '{%s}InstdAmt' % ns)
    instdAmt.attrib['Ccy'] = transfer.currency
    instdAmt.text = str(transfer.instructed_amount)

    cdtrAgt = ET.SubElement(cdtTrfTxInf, '{%s}CdtrAgt' % ns)
    finInstnId_cdtrAgt = ET.SubElement(cdtrAgt, '{%s}FinInstnId' % ns)
    if transfer.creditor_agent.bic:
        ET.SubElement(finInstnId_cdtrAgt, '{%s}BIC' % ns).text = transfer.creditor_agent.bic

    cdtr = ET.SubElement(cdtTrfTxInf, '{%s}Cdtr' % ns)
    ET.SubElement(cdtr, '{%s}Nm' % ns).text = transfer.creditor.name

    cdtrAcct = ET.SubElement(cdtTrfTxInf, '{%s}CdtrAcct' % ns)
    id_cdtrAcct = ET.SubElement(cdtrAcct, '{%s}Id' % ns)
    ET.SubElement(id_cdtrAcct, '{%s}IBAN' % ns).text = transfer.creditor_account.iban

    if transfer.remittance_information_unstructured:
        rmtInf = ET.SubElement(cdtTrfTxInf, '{%s}RmtInf' % ns)
        ET.SubElement(rmtInf, '{%s}Ustrd' % ns).text = transfer.remittance_information_unstructured

    xml_filename = f"pain_001_{transfer.payment_id}.xml"
    xml_path = os.path.join(SCHEMA_DIR, xml_filename)
    ET.ElementTree(document).write(xml_path, encoding='utf-8', xml_declaration=True)

    return xml_path

def generate_aml_file(transfer):
    aml = ET.Element('AMLRequest')
    aml.attrib['xmlns'] = 'http://example.com/aml'

    transaction = ET.SubElement(aml, 'Transaction')
    ET.SubElement(transaction, 'MessageID').text = generate_message_id('AML')
    ET.SubElement(transaction, 'PaymentID').text = transfer.payment_id
    ET.SubElement(transaction, 'DebtorName').text = transfer.debtor.name
    ET.SubElement(transaction, 'DebtorIBAN').text = transfer.debtor_account.iban
    ET.SubElement(transaction, 'CreditorName').text = transfer.creditor.name
    ET.SubElement(transaction, 'CreditorIBAN').text = transfer.creditor_account.iban
    ET.SubElement(transaction, 'Amount').text = str(transfer.instructed_amount)
    ET.SubElement(transaction, 'Currency').text = transfer.currency

    aml_tree = ET.ElementTree(aml)

    aml_filename = f"AML_{transfer.payment_id}.xml"
    aml_path = os.path.join(SCHEMA_DIR, aml_filename)
    aml_tree.write(aml_path, encoding='utf-8', xml_declaration=True)

    return aml_path


# ===========================
# ENVIO DE TRANSFERENCIAS
# ===========================

def send_transfer(transfer, use_token=None, use_otp=None, regenerate_token=False, regenerate_otp=False):
    payment_id = transfer.payment_id
    # Generar archivos
    xml_path = generate_pain_001(transfer)
    aml_path = generate_aml_file(transfer)

    with open(xml_path, 'r', encoding='utf-8') as xml_file:
        xml_content = xml_file.read()
    with open(aml_path, 'r', encoding='utf-8') as aml_file:
        aml_content = aml_file.read()
        
    # # Obtener OTP dinámico basado en la transferencia
    # otp_tokenG = get_otp_for_transfer(transfer)
    # otp_tokenF = '02569S'
    # otp_token = otp_tokenG if OTP_MODE == 'G' else otp_tokenF
    
    # Obtener Token
    token = get_access_token() if regenerate_token else use_token
    if not token:
        raise Exception("No se proporcionó TOKEN ni se solicitó generar uno nuevo.")
    
    # Obtener OTP
    otp = get_otp_for_transfer(transfer, token) if regenerate_otp else use_otp
    if not otp:
        raise Exception("No se proporcionó OTP ni se solicitó generar uno nuevo.")
    
    # Preparar headers
    headers = default_request_headers()
    headers.update({
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json',
        'idempotency-id': payment_id,
        'otp': otp,
    })

    # Construir body
    body = {
        "debtor": {
            "debtorName": transfer.debtor.name
        },
        "debtorAccount": {
            "iban": transfer.debtor_account.iban,
            "currency": transfer.debtor_account.currency
        },
        "creditor": {
            "creditorName": transfer.creditor.name
        },
        "creditorAccount": {
            "iban": transfer.creditor_account.iban,
            "currency": transfer.creditor_account.currency
        },
        "creditorAgent": {
            "financialInstitutionId": transfer.creditor_agent.financial_institution_id or ""
        },
        "instructedAmount": {
            "amount": float(transfer.instructed_amount),
            "currency": transfer.currency
        },
        "requestedExecutionDate": transfer.requested_execution_date.strftime('%Y-%m-%d'),
        "remittanceInformationUnstructured": transfer.remittance_information_unstructured or "Pago"
    }

    # Enviar petición
    response = requests.post(BANK_API_URL, json=body, headers=headers)

    # Guardar en logs
    save_log(
        payment_id,
        request_headers=headers,
        request_body=body,
        response_headers=dict(response.headers),
        response_body=response.text
    )

    # Actualizar estado de la transferencia
    if response.status_code == 201:
        transfer.status = 'ENVIADO'
    else:
        transfer.status = 'ERROR'
    transfer.save()

    return response

