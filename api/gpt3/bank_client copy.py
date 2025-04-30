import json
import requests
import logging
import os
import xml.etree.ElementTree as ET
from cryptography.fernet import Fernet
from lxml import etree

from .utils2 import (
    HEADERS_DEFAULT,
    TIMEOUT_REQUEST,
    obtener_ruta_schema_transferencia,
    registrar_log,
    handle_error_response
)

# Logger para toda esta utilidad
logger = logging.getLogger(__name__)

# Configuraciones
TIMEOUT = (5, 5)  # (connect_timeout, read_timeout)
RETRY_COUNT = 3
RETRY_DELAY = 2

LOGS_DIR = os.path.join("schemas", "transferencias")
SCHEMA_DIR = os.path.join("schemas", "transferencias")

KEY_FILE =os.path.join(SCHEMA_DIR, 'secret.key')
SCHEMA_PATH = os.path.join(SCHEMA_DIR, 'pain.002.001.03.xsd')
SCHEMA_PATH_PAIN001 = os.path.join(SCHEMA_DIR, 'pain.001.001.03.xsd')

# Asegurar que existan los directorios
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SCHEMA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)

URL = "https://api.db.com/gw/dbapi/banking/transactions/v2"

URL2 = "https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer"
URL3 = "https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"


# Función para obtener clave de cifrado de logs (o crearla)
def get_encryption_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
    else:
        with open(KEY_FILE, 'rb') as key_file:
            key = key_file.read()
    return Fernet(key)

encryptor = get_encryption_key()


# Función para ocultar OTP en logs
def mask_otp(otp):
    if len(otp) <= 4:
        return '**' + otp[-2:]
    return otp[:2] + '**' + otp[-2:]


# Función para guardar logs cifrados
def save_log1(payment_id, content):
    filepath = os.path.join(LOGS_DIR, f'transferencia_{payment_id}.log')
    encrypted_content = encryptor.encrypt(content.encode('utf-8'))
    with open(filepath, 'wb') as f:
        f.write(encrypted_content)


# Función para guardar logs sin encriptar
def save_log2(payment_id, content):
    filepath = os.path.join(LOGS_DIR, f'transferencia_{payment_id}.log')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


# Función para validar un XML contra el esquema pain.002
def validate_pain002(xml_text):
    try:
        xml_doc = etree.fromstring(xml_text.encode('utf-8'))
        with open(SCHEMA_PATH, 'rb') as schema_file:
            schema_doc = etree.parse(schema_file)
            schema = etree.XMLSchema(schema_doc)
        schema.assertValid(xml_doc)
        print("\u2705 XML pain.002 validado exitosamente.")
    except etree.XMLSchemaError as e:
        raise Exception(f"\u274C Error de validaci\u00f3n en pain.002: {str(e)}")
    except etree.XMLSyntaxError as e:
        raise Exception(f"\u274C Error de sintaxis XML: {str(e)}")


# Función para validar XML pain.001 contra el XSD oficial
def validate_pain001(xml_text):
    try:
        xml_doc = etree.fromstring(xml_text.encode('utf-8'))
        with open(SCHEMA_PATH_PAIN001, 'rb') as schema_file:
            schema_doc = etree.parse(schema_file)
            schema = etree.XMLSchema(schema_doc)
        schema.assertValid(xml_doc)
        print("\u2705 XML pain.001 validado exitosamente.")
    except etree.XMLSchemaError as e:
        raise Exception(f"\u274C Error de validaci\u00f3n en pain.001: {str(e)}")
    except etree.XMLSyntaxError as e:
        raise Exception(f"\u274C Error de sintaxis XML: {str(e)}")


# Función principal para enviar una transferencia SEPA
def send_sepa_transfer(payment_id, payload, otp, access_token):
    headers = build_complete_sepa_headers({
        'otp': otp,
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': payment_id
    }, 'POST')  # Construir headers usando build_complete_sepa_headers
    url = f'{URL}'
    return _post_request(url, payment_id, payload, headers)


# Función para obtener el estado de una transferencia SEPA
def get_sepa_transfer_status(payment_id, access_token):
    url = f'{URL}/{payment_id}/status'
    headers = build_complete_sepa_headers({
        'Authorization': f'Bearer {access_token}',
    }, 'GET')  # Construir headers usando build_complete_sepa_headers
    return _send_request('GET', url, headers, None, payment_id)


# Función para cancelar una transferencia SEPA
def cancel_sepa_transfer(payment_id, otp, access_token):
    url = f'{URL}/{payment_id}'
    headers = build_complete_sepa_headers({
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': payment_id,
        'otp': otp,
    }, 'DELETE')  # Construir headers usando build_complete_sepa_headers
    return _delete_request(url, payment_id, otp, access_token)


# Función para reintentar second factor authentication
def retry_second_factor(payment_id, payload, otp, access_token):
    url = f'{URL}/{payment_id}'
    headers = build_complete_sepa_headers({
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': payment_id,
        'otp': otp,
    }, 'PATCH')  # Construir headers usando build_complete_sepa_headers
    return _patch_request(url, payment_id, payload, otp, access_token)


# Funciones internas genericas

def _post_request(url, payment_id, payload, headers):
    # Llama a _send_request con el método POST
    return _send_request('POST', url, headers, payload, payment_id)


def _get_request(url, payment_id, access_token):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
    }
    # Llama a _send_request con el método GET
    return _send_request('GET', url, headers, None, payment_id)


def _delete_request(url, payment_id, otp, access_token):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': payment_id,
        'otp': otp,
    }
    # Llama a _send_request con el método DELETE
    return _send_request('DELETE', url, headers, None, payment_id)


def _patch_request(url, payment_id, payload, otp, access_token):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'idempotency-id': payment_id,
        'otp': otp,
    }
    # Llama a _send_request con el método PATCH
    return _send_request('PATCH', url, headers, payload, payment_id)


def _send_request(method, url, headers, payload, payment_id):
    session = requests.Session()
    attempt = 0
    while attempt < RETRY_COUNT:
        try:
            # Selecciona el método HTTP adecuado
            if method == 'POST':
                response = session.post(url, json=payload, headers=headers, timeout=TIMEOUT)
            elif method == 'GET':
                response = session.get(url, headers=headers, timeout=TIMEOUT)
            elif method == 'DELETE':
                response = session.delete(url, headers=headers, timeout=TIMEOUT)
            elif method == 'PATCH':
                response = session.patch(url, json=payload, headers=headers, timeout=TIMEOUT)
            else:
                raise ValueError("Método HTTP no soportado.")

            # Guarda los logs de la solicitud y la respuesta
            request_info = f"Request Headers: {headers}\nPayload: {payload}"
            response_info = f"Response Status: {response.status_code}\nResponse Headers: {dict(response.headers)}\nResponse Body: {response.text}"
            registrar_log(payment_id, headers, response.text)

            # Valida el XML si el contenido es de tipo XML
            if 'xml' in response.headers.get('Content-Type', ''):
                validate_pain002(response.text)

            # Verifica si la respuesta tiene errores
            if response.status_code not in [200, 201]:
                mensaje = handle_error_response(response)
                registrar_log(payment_id, headers, response.text, error=mensaje)
                return {"error": mensaje}

            return response  # Devuelve el objeto response completo
        except requests.RequestException as e:
            # Manejo de errores y reintentos
            carpeta_transferencia = os.path.join(LOGS_DIR, str(payment_id))
            os.makedirs(carpeta_transferencia, exist_ok=True)
            error_log_path = os.path.join(carpeta_transferencia, f"error_{payment_id}.log")
            with open(error_log_path, 'a', encoding='utf-8') as error_file:
                error_file.write(f"Intento {attempt + 1} fallido: {str(e)}\n")
            registrar_log(payment_id, headers, "", error=str(e))
            logging.error(f"Intento {attempt + 1} fallido: {e}")
            attempt += 1
            if attempt >= RETRY_COUNT:
                return {"error": "No se pudo completar la operación tras varios intentos."}


