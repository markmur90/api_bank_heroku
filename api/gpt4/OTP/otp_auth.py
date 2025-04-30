import hashlib
import json
import os
import logging
from datetime import datetime, timezone
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

from api.gpt4.generate_xml import generar_xml_pain001, validar_xml_con_xsd, validar_xml_pain001

logger = logging.getLogger(__name__)

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

OTP_MODE = 'F'
OTP_URL = DEUTSCHE_BANK_OTP_URL

tokenF = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"
tokenMk = "H858hfhg0ht40588hhfjpfhhd9944940jf"
TOKEN = tokenMk

CLIENT_ID = DEUTSCHE_BANK_CLIENT_ID
CLIENT_SECRET = DEUTSCHE_BANK_CLIENT_SECRET
TOKEN_URL = DEUTSCHE_BANK_TOKEN_URL

def crear_challenge_autorizacion(transfer, token):
    schema_data = transfer.to_schema_data()
    request_type, request_data = preparar_request_type_y_datos(schema_data)

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': generate_correlation_id(),
    }

    payload = {
        "method": "PHOTOTAN",
        "requestType": request_type,
        "requestData": request_data,
        "language": "es"
    }

    try:
        response = requests.post(
            "https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges",
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code != 201:
            error_msg = handle_error_response(response)
            registrar_log(transfer.payment_id, headers, response.text, error=error_msg)
            raise Exception(error_msg)
        return response.json()["id"]
    except requests.RequestException as e:
        registrar_log(transfer.payment_id, headers, error=str(e))
        raise Exception(f"Error de conexión al crear challenge: {e}")

def resolver_challenge(challenge_id, token, payment_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Correlation-Id': generate_correlation_id(),
    }

    payload = {
        "challengeResponse": "123456"
    }

    try:
        response = requests.patch(
            f"https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges/{challenge_id}",
            headers=headers,
            json=payload,
            timeout=10
        )
        if response.status_code != 200:
            error_msg = handle_error_response(response)
            registrar_log(payment_id, headers, response.text, error=error_msg)
            raise Exception(error_msg)
        return response.json()["challengeProofToken"]
    except requests.RequestException as e:
        registrar_log(payment_id, headers, error=str(e))
        raise Exception(f"Error de conexión al resolver challenge: {e}")

def obtener_otp_automatico_con_challenge(transfer):
    token = get_access_token()
    challenge_id = crear_challenge_autorizacion(transfer, token)
    otp_token = resolver_challenge(challenge_id, token, transfer.payment_id)
    return otp_token, token
