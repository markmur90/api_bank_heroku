import os
import logging
import time
import random
import string
import uuid
import requests
from datetime import datetime
from django.conf import settings
import xml.etree.ElementTree as ET

TRANSFER_LOG_DIR = os.path.join(settings.BASE_DIR, 'logs', 'transferencias')
SCHEMA_DIR = os.path.join(settings.BASE_DIR, 'schemas')
os.makedirs(TRANSFER_LOG_DIR, exist_ok=True)
os.makedirs(SCHEMA_DIR, exist_ok=True)

# URLs de Deutsche Bank
DEUTSCHE_BANK_CLIENT_ID = '...'
DEUTSCHE_BANK_CLIENT_SECRET = '...'
DEUTSCHE_BANK_TOKEN_URL = 'https://api.db.com:443/gw/oidc/token'
DEUTSCHE_BANK_OTP_URL = 'https://api.db.com:443/gw/dbapi/others/onetimepasswords/v2/single'
BANK_API_URL = 'https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer'

# Variables internas
_access_token = None
_token_expiry = 0

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
    logger.info('=========== PETICIÓN ===========')
    if request_headers:
        logger.info(f'Headers de petición: {request_headers}')
    if request_body:
        logger.info(f'Cuerpo de petición: {request_body}')
    logger.info('=========== RESPUESTA ===========')
    if response_headers:
        logger.info(f'Headers de respuesta: {response_headers}')
    if response_body:
        logger.info(f'Cuerpo de respuesta: {response_body}')

def generate_unique_code(length=35):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_message_id(prefix='MSG'):
    return f"{prefix}-{generate_unique_code(20)}"

def generate_instruction_id():
    return generate_unique_code(20)

def generate_end_to_end_id():
    return generate_unique_code(30)

def generate_correlation_id():
    return str(uuid.uuid4())

def get_access_token():
    global _access_token, _token_expiry
    current_time = time.time()
    if _access_token and current_time < _token_expiry - 60:
        return _access_token

    data = {
        'grant_type': 'client_credentials',
        'scope': 'instant_sepa_credit_transfers'
    }
    auth = (DEUTSCHE_BANK_CLIENT_ID, DEUTSCHE_BANK_CLIENT_SECRET)
    retries = 3
    while retries > 0:
        try:
            response = requests.post(DEUTSCHE_BANK_TOKEN_URL, data=data, auth=auth, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                _access_token = token_data['access_token']
                _token_expiry = current_time + token_data.get('expires_in', 3600)
                return _access_token
        except requests.RequestException as e:
            print(f"Error obteniendo token: {e}")
        retries -= 1
        time.sleep(2)
    raise Exception("Error: No se pudo obtener token después de varios intentos.")

def get_otp_for_transfer(transfer, token):
    headers = {
        'Authorization': f'Bearer {token}',
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
            response = requests.post(DEUTSCHE_BANK_OTP_URL, json=body, headers=headers, timeout=10)
            if response.status_code == 201:
                otp_data = response.json()
                return otp_data['id']
        except requests.RequestException as e:
            print(f"Error solicitando OTP: {e}")
        retries -= 1
        time.sleep(2)
    raise Exception("Error: No se pudo obtener OTP.")

def send_transfer(transfer, use_token=None, use_otp=None, regenerate_token=False, regenerate_otp=False):
    payment_id = transfer.payment_id
    # Generar archivos XML
    xml_path = generate_pain_001(transfer)
    aml_path = generate_aml_file(transfer)

    with open(xml_path, 'r', encoding='utf-8') as xml_file:
        xml_content = xml_file.read()
    with open(aml_path, 'r', encoding='utf-8') as aml_file:
        aml_content = aml_file.read()

    # Obtener Token
    token = get_access_token() if regenerate_token else use_token
    if not token:
        raise Exception("No se proporcionó TOKEN ni se solicitó generar uno nuevo.")

    # Obtener OTP
    otp = get_otp_for_transfer(transfer, token) if regenerate_otp else use_otp
    if not otp:
        raise Exception("No se proporcionó OTP ni se solicitó generar uno nuevo.")

    headers = default_request_headers()
    headers.update({
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'idempotency-id': payment_id,
        'otp': otp
    })

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

    response = requests.post(BANK_API_URL, json=body, headers=headers)
    
    save_log(payment_id, headers, body, dict(response.headers), response.text)
    return response

