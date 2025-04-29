import json
import os
import re
import logging
import uuid
import qrcode

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
import requests
from requests_oauthlib import OAuth2Session
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
from reportlab.lib.utils import ImageReader
from jsonschema import validate, ValidationError
from requests.structures import CaseInsensitiveDict

from api.gpt3.bank_client import validate_pain001
from api.gpt3.helpers import obtener_ruta_schema_transferencia
from api.gpt3.models import SepaCreditTransfer

logger = logging.getLogger(__name__)

# Token de acceso dummy (debería obtenerse con autenticación OAuth real)
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

ORIGIN = "https://api.db.com"

API_CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
API_CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'

DEUTSCHE_BANK_CLIENT_ID='SE0IWHFHJFHB848R9E0R9FRUFBCJHW0W9FHF008E88W0457338ASKH64880'
DEUTSCHE_BANK_CLIENT_SECRET='H858hfhg0ht40588hhfjpfhhd9944940jf'

CLIENT_ID = API_CLIENT_ID
CLIENT_SECRET = API_CLIENT_SECRET

DEFAULT_APIKEY = getattr(settings, "APIKEY", "MI_API_KEY")

LOGS_DIR = os.path.join("schemas", "transferencias")
os.makedirs(LOGS_DIR, exist_ok=True)



def build_complete_sepa_headers(request, method: str):
    """
    Construye las cabeceras completas para una solicitud SEPA.

    Args:
        request: Objeto de solicitud HTTP.
        method (str): Método HTTP (e.g., 'POST', 'GET', 'PATCH', 'DELETE').

    Returns:
        CaseInsensitiveDict: Objeto con las cabeceras completas.
    """
    method = method.upper()
    headers = CaseInsensitiveDict()

    # Cabecera idempotency-id (obligatoria para POST y GET)
    headers['idempotency-id'] = request.headers.get('idempotency-id', str(uuid.uuid4()))

    # Cabecera OTP (obligatoria para POST, PATCH, DELETE)
    if method in ['POST', 'PATCH', 'DELETE']:
        headers['otp'] = request.POST.get('otp') if method == 'POST' else request.headers.get('otp', 'SEPA_TRANSFER_GRANT')

    # Cabecera Correlation-Id (opcional, pero se genera un valor predeterminado si no está presente)
    headers['Correlation-Id'] = request.headers.get('Correlation-Id', str(uuid.uuid4()))

    # Cabecera x-request-id (obligatoria, se genera un UUID si no está presente)
    headers['x-request-id'] = request.headers.get('x-request-id', str(uuid.uuid4()))

    # Cabecera Origin (obligatoria)
    headers['Origin'] = request.headers.get('Origin', ORIGIN)

    # Cabecera X-Requested-With (obligatoria)
    headers['X-Requested-With'] = "XMLHttpRequest"

    # Cabecera Authorization (obligatoria)
    headers['Authorization'] = f"Bearer {ACCESS_TOKEN}"

    # Cabecera Accept (obligatoria)
    headers['Accept'] = "application/json"

    # Cabecera Content-Type (obligatoria para POST y PATCH)
    if method in ['POST', 'PATCH']:
        headers['Content-Type'] = "application/json"

    # Cabeceras opcionales
    process_id = request.headers.get('process-id')
    if process_id:
        headers['process-id'] = process_id

    preview_sig = request.headers.get('previewsignature')
    if preview_sig:
        headers['previewsignature'] = preview_sig

    # Validar cabeceras antes de devolverlas
    errors = validate_headers(headers)
    if errors:
        raise ValueError(f"Errores en las cabeceras: {', '.join(errors)}")

    return headers


def handle_error_response(response):
    """Maneja los códigos de error específicos de la API."""
    error_messages = {
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
    error_code = response.status_code
    return error_messages.get(error_code, f"Error desconocido: {response.text}")


OAUTH_CONFIG = {
    'client_id': str(CLIENT_ID),
    'client_secret': str(CLIENT_SECRET),
    'token_url': 'https://api.db.com/gw/oidc/token',
    'authorization_url': 'https://api.db.com/gw/oidc/authorize',
    'scopes': ['sepa_credit_transfers'],
    'access_token': str(ACCESS_TOKEN),
}


def get_oauth_session(request):
    """Crea sesión OAuth2 utilizando el access_token del entorno"""
    if not ACCESS_TOKEN:
        logger.error("ACCESS_TOKEN no está configurado en las variables de entorno")
        raise ValueError("ACCESS_TOKEN no está configurado")

    # Crear sesión OAuth2 con el token de acceso
    return OAuth2Session(client_id=OAUTH_CONFIG['client_id'], token={'access_token': ACCESS_TOKEN, 'token_type': 'Bearer'})


def generar_pdf_transferencia(transferencia):
    creditor_name = transferencia.creditor.creditor_name.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payment_reference = transferencia.payment_id
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_reference)
    pdf_filename = f"{creditor_name}_{timestamp}_{payment_reference}.pdf"
    pdf_path = os.path.join(carpeta_transferencia, pdf_filename)

    # Crear canvas PDF
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
        ["Name", transferencia.debtor.debtor_name],
        ["IBAN", transferencia.debtor_account.iban],
        ["Customer ID", transferencia.debtor.customer_id],
        ["Address", f"{transferencia.debtor.postal_address.street_and_house_number}, {transferencia.debtor.postal_address.zip_code_and_city}, {transferencia.debtor.postal_address.country}"]
    ]
    crear_tabla_pdf(c, debtor_data, current_y)
    current_y -= 120

    # Tabla Acreedor
    creditor_data = [
        ["Creditor Information", ""],
        ["Name", transferencia.creditor.creditor_name],
        ["IBAN", transferencia.creditor_account.iban],
        ["BIC", transferencia.creditor_agent.financial_institution_id],
        ["Address", f"{transferencia.creditor.postal_address.street_and_house_number}, {transferencia.creditor.postal_address.zip_code_and_city}, {transferencia.creditor.postal_address.country}"]
    ]
    crear_tabla_pdf(c, creditor_data, current_y)
    current_y -= 200

    # Tabla Transferencia
    transfer_data = [
        ["Transfer Details", ""],
        ["Amount", f"{transferencia.instructed_amount.amount} {transferencia.instructed_amount.currency}"],
        ["Requested Execution Date", transferencia.requested_execution_date.strftime('%d/%m/%Y')],
        ["Purpose Code", transferencia.purpose_code],
        ["Remittance Info (Structured)", transferencia.remittance_information_structured or 'N/A'],
        ["Remittance Info (Unstructured)", transferencia.remittance_information_unstructured or 'N/A'],
        ["Auth ID", transferencia.auth_id or 'N/A'],
        ["Transaction Status", transferencia.transaction_status],
        ["Priority", "High (Instant SEPA Credit Transfer)"]
    ]
    crear_tabla_pdf(c, transfer_data, current_y)
    current_y -= 200

    # Generar QR Code con Payment ID
    qr = qrcode.make(transferencia.payment_id)
    qr_path = os.path.join(carpeta_transferencia, f"qr_{payment_reference}.png")
    qr.save(qr_path)

    # Insertar QR en una página separada
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2.0, height - 80, "Scan to verify Payment ID")
    qr_image = ImageReader(qr_path)
    c.drawImage(qr_image, width / 2.0 - 75, height / 2.0 - 75, width=150, height=150, preserveAspectRatio=True)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2.0, 50, "Generated automatically by SEPA Transfer System.")

    # # Incluir contenido del pain.001 en una página separada
    # xml_path = os.path.join(carpeta_transferencia, f"pain001_{payment_reference}.xml")
    # if os.path.exists(xml_path):
    #     c.showPage()
    #     c.setFont("Helvetica-Bold", 14)
    #     c.drawCentredString(width / 2.0, height - 50, "Pain.001 Response Details")
    #     current_y = height - 80
    #     c.setFont("Helvetica", 10)

    #     with open(xml_path, "r", encoding="utf-8") as xml_file:
    #         xml_lines = xml_file.readlines()

    #     for line in xml_lines:
    #         if current_y < 80:
    #             c.showPage()
    #             c.setFont("Helvetica", 10)
    #             current_y = height - 80
    #         # Formatear el contenido del XML para hacerlo más legible y justificarlo
    #         formatted_line = line.strip().replace("<", "&lt;").replace(">", "&gt;")
    #         wrapped_lines = c.beginText(50, current_y)
    #         wrapped_lines.setFont("Helvetica", 10)
    #         wrapped_lines.setTextOrigin(50, current_y)
    #         wrapped_lines.setWordSpace(0.5)
    #         wrapped_lines.textLines(formatted_line)
    #         c.drawText(wrapped_lines)
    #         current_y -= 12 * len(formatted_line.splitlines())

    # Guardar PDF
    c.save()

    # Limpiar QR temporal
    if os.path.exists(qr_path):
        os.remove(qr_path)

    return pdf_path


def crear_tabla_pdf(c, data, y_position):
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


def validate_headers(headers):
    errors = []
    idempotency_id = headers.get('idempotency-id', '')
    if not isinstance(idempotency_id, str):
        idempotency_id = str(idempotency_id)
        
    if 'idempotency-id' not in headers or not re.match(r'^[A-Fa-f0-9\-]{36}$', idempotency_id):
        errors.append("Cabecera 'idempotency-id' es requerida y debe ser un UUID válido.")
        
    if 'otp' not in headers or not headers.get('otp'):
        errors.append("Cabecera 'otp' es requerida.")
        
    correlation_id = headers.get('Correlation-Id')
    if correlation_id is not None and len(correlation_id) > 50:
        errors.append("Cabecera 'Correlation-Id' no debe exceder los 50 caracteres.")
        
    if 'apikey' not in headers or not headers.get('apikey'):
        errors.append("Cabecera 'apikey' es requerida.")
        
    if 'process-id' in headers and not headers.get('process-id'):
        errors.append("Cabecera 'process-id' no debe estar vacía si está presente.")
        
    if 'previewsignature' in headers and not headers.get('previewsignature'):
        errors.append("Cabecera 'previewsignature' no debe estar vacía si está presente.")
        
    if 'Origin' not in headers or not headers.get('Origin'):
        errors.append("Cabecera 'Origin' es requerida.")
        
    if 'x-request-id' not in headers or not re.match(r'^[A-Fa-f0-9\-]{36}$', headers.get('x-request-id', '')):
        errors.append("Cabecera 'x-request-id' es requerida y debe ser un UUID válido.")
        
    return errors


def build_headers1(request, external_method):

    method = external_method.upper()
    headers = {}
    
    # Cabecera idempotency-id
    if method in ['POST', 'GET']:
        headers['idempotency-id'] = request.headers.get('idempotency-id', str(uuid.uuid4()))
    else:
        headers['idempotency-id'] = request.headers.get('idempotency-id')
    
    # Cabecera OTP
    if method == 'POST':
        headers['otp'] = request.POST.get('otp', 'SEPA_TRANSFER_GRANT')
    elif method in ['PATCH', 'DELETE']:
        headers['otp'] = request.headers.get('otp')
    
    # Cabecera Correlation-Id
    if method == 'POST':
        headers['Correlation-Id'] = request.headers.get('Correlation-Id', str(uuid.uuid4()))
    else:
        corr_id = request.headers.get('Correlation-Id')
        if corr_id:
            headers['Correlation-Id'] = corr_id
    
    # Cabecera apikey
    headers['apikey'] = request.headers.get('apikey')
    
    # Cabeceras opcionales process-id y previewsignature (solo en flujos con segundo factor)
    process_id = request.headers.get('process-id')
    if process_id:
        headers['process-id'] = process_id
        
    preview_sig = request.headers.get('previewsignature')
    if preview_sig:
        headers['previewsignature'] = preview_sig
    
    # Cabecera x-request-id (UUID único por solicitud)
    xreq = request.headers.get('x-request-id')
    if not xreq:
        xreq = str(uuid.uuid4())
    headers['x-request-id'] = xreq
    
    # Cabeceras de control de solicitud (CORS y contexto de petición)
    headers['Origin'] = ORIGIN
    headers['X-Requested-With'] = 'XMLHttpRequest'
    return headers


def attach_common_headers(headers, external_method):
    headers['Authorization'] = f"Bearer {ACCESS_TOKEN}"
    headers['Accept'] = 'application/json'
    if external_method.upper() in ['POST', 'PATCH']:
        headers['Content-Type'] = 'application/json'
    return headers


def validate_parameters(data):
    errors = []
    if 'iban' in data and not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$', data['iban']):
        errors.append("El IBAN proporcionado no es válido.")
        
    if 'requestedExecutionDate' in data:
        try:
            datetime.strptime(data['requestedExecutionDate'], '%Y-%m-%d')
        except ValueError:
            errors.append("El formato de 'requestedExecutionDate' debe ser yyyy-MM-dd.")
            
    if 'createDateTime' in data:
        try:
            datetime.strptime(data['createDateTime'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            errors.append("El formato de 'createDateTime' debe ser yyyy-MM-dd'T'HH:mm:ss.")
            
    if 'currency' in data and not re.match(r'^[A-Z]{3}$', data['currency']):
        errors.append("La moneda debe ser un código ISO 4217 válido (ejemplo: EUR).")
        
    if 'amount' in data and (not isinstance(data['amount'], (int, float)) or data['amount'] <= 0):
        errors.append("El monto debe ser un número positivo.")
        
    if 'transactionStatus' in data and data['transactionStatus'] not in ['RJCT', 'RCVD', 'ACCP', 'ACTC', 'ACSP', 'ACSC', 'ACWC', 'ACWP', 'ACCC', 'CANC', 'PDNG']:
        errors.append("El estado de la transacción no es válido.")
        
    if 'action' in data and data['action'] not in ['CREATE', 'CANCEL']:
        errors.append("El valor de 'action' no es válido. Valores permitidos: 'CREATE', 'CANCEL'.")
        
    if 'chargeBearer' in data and len(data['chargeBearer']) > 35:
        errors.append("El valor de 'chargeBearer' no debe exceder los 35 caracteres.")
        
    return errors



def construir_payload(transferencia: SepaCreditTransfer) -> dict:
    payload = {
        "debtor": {
            "debtorName": transferencia.debtor.debtor_name,
            "debtorPostalAddress": {
                "country": transferencia.debtor.postal_address.country,
                "addressLine": {
                    "streetAndHouseNumber": transferencia.debtor.postal_address.street_and_house_number,
                    "zipCodeAndCity": transferencia.debtor.postal_address.zip_code_and_city
                }
            }
        },
        "debtorAccount": {
            "iban": transferencia.debtor_account.iban,
            "currency": transferencia.debtor_account.currency
        },
        "creditor": {
            "creditorName": transferencia.creditor.creditor_name,
            "creditorPostalAddress": {
                "country": transferencia.creditor.postal_address.country,
                "addressLine": {
                    "streetAndHouseNumber": transferencia.creditor.postal_address.street_and_house_number,
                    "zipCodeAndCity": transferencia.creditor.postal_address.zip_code_and_city
                }
            }
        },
        "creditorAccount": {
            "iban": transferencia.creditor_account.iban,
            "currency": transferencia.creditor_account.currency
        },
        "creditorAgent": {
            "financialInstitutionId": transferencia.creditor_agent.financial_institution_id
        },
        "instructedAmount": {
            "amount": float(transferencia.instructed_amount.amount),
            "currency": transferencia.instructed_amount.currency
        },
        "paymentIdentification": {
            "endToEndIdentification": transferencia.payment_identification.end_to_end_id,
            "instructionId": transferencia.payment_identification.instruction_id
        },
        "purposeCode": transferencia.purpose_code,
        "requestedExecutionDate": transferencia.requested_execution_date.strftime("%Y-%m-%d"),
        "remittanceInformationStructured": transferencia.remittance_information_structured,
        "remittanceInformationUnstructured": transferencia.remittance_information_unstructured,
    }

    # ⚡ Opcionales: Si tienes configurado payment_type_information
    if transferencia.payment_type_information:
        payload["paymentTypeInformation"] = {
            "serviceLevel": {
                "serviceLevelCode": transferencia.payment_type_information.service_level_code
            },
            "localInstrument": {
                "localInstrumentCode": transferencia.payment_type_information.local_instrument_code
            } if transferencia.payment_type_information.local_instrument_code else None,
            "categoryPurpose": {
                "categoryPurposeCode": transferencia.payment_type_information.category_purpose_code
            } if transferencia.payment_type_information.category_purpose_code else None
        }

        # Limpieza por si opcionales vienen en None
        payload["paymentTypeInformation"] = {k: v for k, v in payload["paymentTypeInformation"].items() if v}

    return payload



def build_headers(idempotency_id=None, otp=None, correlation_id=None):
    headers = {
        "Accept": "text/html, application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
    }
    if idempotency_id:
        headers["idempotency-id"] = idempotency_id
    if otp:
        headers["otp"] = otp
    if correlation_id:
        headers["Correlation-Id"] = correlation_id
    return headers


def validate_schema(data, schema):
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        return False, str(e)


def save_log(payment_id, request_headers, response_headers, response_text):
    """Guarda un log completo por transferencia"""
    log_path = os.path.join(LOGS_DIR, f"transferencia_{payment_id}.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"--- Request Headers ---\n{json.dumps(request_headers, indent=2)}\n")
        f.write(f"\n--- Response Headers ---\n{json.dumps(dict(response_headers), indent=2)}\n")
        f.write(f"\n--- Response Text ---\n{response_text}\n")

def get_log_path(payment_id):
    return os.path.join(LOGS_DIR, f"transferencia_{payment_id}.log")

def log_exists(payment_id):
    """Verifica si existe el archivo de log para el payment_id dado"""
    log_path = get_log_path(payment_id)
    return os.path.isfile(log_path)


HEADERS_DEFAULT = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "es-CO",
    "Connection": "keep-alive",
    "Priority": "u=0, i",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
}

def generar_otp_sepa_transfer():
    url = "https://simulator-api.db.com//gw/dbapi/others/onetimepasswords/v2/single"

    payload = {
        "method": "PUSHTAN",
        "requestType": "SEPA_TRANSFER_GRANT",
        "requestData": {},
        "language": "es"
    }

    try:
        response = requests.post(url, json=payload, headers=HEADERS_DEFAULT, timeout=10)
        response.raise_for_status()

        data = response.json()
        otp_token = data.get('challengeProofToken', None)

        if not otp_token:
            raise Exception("OTP Token no recibido")

        return otp_token
    
    except Exception as e:
        logger.error(f"Error generando OTP: {str(e)}")
        raise
    
    
ORIGIN = "https://api-bank-heroku-72c443ab11d3.herokuapp.com/"
TIMEOUT_REQUEST = 10

with open(os.path.join(settings.BASE_DIR, 'schemas', 'sepaCreditTransferRequestSchema.json')) as f:
    TRANSFERENCIA_SCHEMA = json.load(f)


HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
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
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Origin": ORIGIN  # Cambiar la dirección fija por el campo ORIGIN
}


# api/gpt3/utils.py

def obtener_otp_para_transferencia(access_token, payment_id, transferencia):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    url = "https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges"

    payload = {
        "method": "PUSHTAN",   # O "PHOTOTAN" si usas imagen
        "requestType": "SEPA_TRANSFER_GRANT",
        "requestData": {
            "type": "challengeRequestDataSepaPaymentTransfer",
            "targetIban": transferencia.creditor_account.iban,  # IBAN destino
            "amountCurrency": transferencia.instructed_amount.currency,  # Moneda
            "amountValue": float(transferencia.instructed_amount.amount),  # Monto
        },
        "language": "en"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('challengeProofToken')  # OTP para transferir
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Error al obtener OTP: {e}")


# Obtener OTP usando el access_token
def obtener_otp(session):
    try:
        access_token = session.token['access_token']
    except (KeyError, AttributeError):
        return None

    url = "https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges"
    payload = {
        "method": "PUSHTAN",
        "requestType": "SEPA_TRANSFER_GRANT",
        "requestData": {}
    }
    headers = HEADERS.copy()
    headers.update({
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest"
    })

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
        response.raise_for_status()
        
        
        
        if response.status_code == 201:
            otp = response.json().get('challengeProofToken')
            return otp
        else:
            return None
        
    except (requests.RequestException, requests.HTTPError, requests.Timeout, ConnectionError):
        return None

# Registrar logs de operaciones
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

# Preparar payload de transferencia
def preparar_payload_transferencia(transferencia, request=None):
    return {
        "creditor": {
            "creditorName": transferencia.creditor.creditor_name,
            "creditorPostalAddress": {
                "country": transferencia.creditor.postal_address.country,
                "addressLine": {
                    "streetAndHouseNumber": transferencia.creditor.postal_address.street_and_house_number,
                    "zipCodeAndCity": transferencia.creditor.postal_address.zip_code_and_city
                }
            }
        },
        "creditorAccount": {
            "iban": transferencia.creditor_account.iban,
            "currency": transferencia.creditor_account.currency
        },
        "creditorAgent": {
            "financialInstitutionId": transferencia.creditor_agent.financial_institution_id
        },
        "debtor": {
            "debtorName": transferencia.debtor.debtor_name,
            "debtorPostalAddress": {
                "country": transferencia.debtor.postal_address.country,
                "addressLine": {
                    "streetAndHouseNumber": transferencia.debtor.postal_address.street_and_house_number,
                    "zipCodeAndCity": transferencia.debtor.postal_address.zip_code_and_city
                }
            }
        },
        "debtorAccount": {
            "iban": transferencia.debtor_account.iban,
            "currency": transferencia.debtor_account.currency
        },
        "instructedAmount": {
            "amount": float(transferencia.instructed_amount.amount),
            "currency": transferencia.instructed_amount.currency
        },
        "paymentIdentification": {
            "endToEndIdentification": transferencia.payment_identification.end_to_end_id,
            "instructionId": transferencia.payment_identification.instruction_id
        },
        "purposeCode": transferencia.purpose_code,
        "requestedExecutionDate": transferencia.requested_execution_date.strftime('%Y-%m-%d'),
        "remittanceInformationStructured": transferencia.remittance_information_structured,
        "remittanceInformationUnstructured": transferencia.remittance_information_unstructured,
        "paymentTypeInformation": {
            "serviceLevel": {
                "serviceLevelCode": request.POST.get('payment_type_information_service_level', 'INST') if request else 'INST'
            },
            "localInstrument": {
                "localInstrumentCode": request.POST.get('payment_type_information_local_instrument', 'INST') if request else 'INST'
            },
            "categoryPurpose": {
                "categoryPurposeCode": request.POST.get('payment_type_information_category_purpose', 'GDSV') if request else 'GDSV'
            }
        }
    }

# Validar archivo pain.001
def validar_xml_schema(payment_id):
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    pain001_path = os.path.join(carpeta, f"pain001_{payment_id}.xml")
    if os.path.exists(pain001_path):
        with open(pain001_path, 'r', encoding='utf-8') as f:
            contenido_xml = f.read()
            validate_pain001(contenido_xml)

# Guardar pain.002 si el banco responde en XML
def guardar_pain002_si_aplica(response, payment_id):
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    content_type = response.headers.get("Content-Type", "")
    if "xml" in content_type and response.text:
        xml_response_path = os.path.join(carpeta, f"pain002_{payment_id}.xml")
        with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(response.text)
