# api/gpt3/utils.py

import os
import re
import json
import uuid
import logging
import qrcode
import requests

from datetime import datetime
from requests.structures import CaseInsensitiveDict
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from jsonschema import validate, ValidationError
from requests_oauthlib import OAuth2Session

from api.gpt3.helpers import obtener_ruta_schema_transferencia
from api.gpt3.models import SepaCreditTransfer

# Logger para toda esta utilidad
logger = logging.getLogger(__name__)

# Configuraciones iniciales
ORIGIN = "https://api-bank-heroku-72c443ab11d3.herokuapp.com"

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

API_CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
API_CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'

DEUTSCHE_BANK_CLIENT_ID='SE0IWHFHJFHB848R9E0R9FRUFBCJHW0W9FHF008E88W0457338ASKH64880'
DEUTSCHE_BANK_CLIENT_SECRET='H858hfhg0ht40588hhfjpfhhd9944940jf'

CLIENT_ID = API_CLIENT_ID
CLIENT_SECRET = API_CLIENT_SECRET

TIMEOUT_REQUEST = 10

# Directorio de logs
LOGS_DIR = os.path.join("schemas", "transferencias")
os.makedirs(LOGS_DIR, exist_ok=True)

# Headers genéricos base
HEADERS_DEFAULT = {
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
}

# =========================
# 2. Construcción de Headers
# =========================

def build_complete_sepa_headers(request, method: str) -> CaseInsensitiveDict:
    """
    Construye todas las cabeceras requeridas para operar transferencias SEPA.

    Args:
        request: Objeto Django Request.
        method: Método HTTP ('POST', 'GET', 'PATCH', 'DELETE').

    Returns:
        CaseInsensitiveDict: Headers configurados.
    """
    method = method.upper()
    headers = CaseInsensitiveDict()

    headers["idempotency-id"] = request.headers.get("idempotency-id", str(uuid.uuid4()))
    headers["x-request-id"] = request.headers.get("x-request-id", str(uuid.uuid4()))
    headers["Correlation-Id"] = request.headers.get("Correlation-Id", str(uuid.uuid4()))
    headers["Origin"] = request.headers.get("Origin", ORIGIN)
    headers["X-Requested-With"] = "XMLHttpRequest"
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"

    if method in ['POST', 'PATCH', 'DELETE']:
        headers["Content-Type"] = "application/json"
        headers["otp"] = request.POST.get("otp") or request.headers.get("otp", "SEPA_TRANSFER_GRANT")

    # Cabeceras opcionales
    process_id = request.headers.get('process-id')
    if process_id:
        headers['process-id'] = process_id

    preview_sig = request.headers.get('previewsignature')
    if preview_sig:
        headers['previewsignature'] = preview_sig

    # Validamos que estén bien
    errors = validate_headers(headers)
    if errors:
        raise ValueError(f"Errores en headers: {', '.join(errors)}")

    return headers

def build_headers(idempotency_id=None, otp=None, correlation_id=None):
    """
    Construye headers básicos mínimos para una solicitud.
    """
    headers = HEADERS_DEFAULT.copy()
    if idempotency_id:
        headers["idempotency-id"] = idempotency_id
    if otp:
        headers["otp"] = otp
    if correlation_id:
        headers["Correlation-Id"] = correlation_id
    return headers


# ==================================
# 4. Validaciones de Headers Manual
# ==================================

def validate_headers(headers):
    """
    Revisa si las cabeceras importantes están correctas.
    """
    errors = []
    if "idempotency-id" not in headers or not re.match(r'^[A-Fa-f0-9\-]{36}$', str(headers.get('idempotency-id', ''))):
        errors.append("Cabecera 'idempotency-id' es obligatoria y debe ser UUID.")
    if "otp" in headers and not headers["otp"]:
        errors.append("Cabecera 'otp' no puede estar vacía si se envía.")
    if "Correlation-Id" in headers and len(headers["Correlation-Id"]) > 50:
        errors.append("Cabecera 'Correlation-Id' debe ser máximo 50 caracteres.")
    if "Origin" not in headers or not headers.get("Origin"):
        errors.append("Cabecera 'Origin' es obligatoria.")
    if "x-request-id" not in headers or not re.match(r'^[A-Fa-f0-9\-]{36}$', str(headers.get('x-request-id', ''))):
        errors.append("Cabecera 'x-request-id' debe ser UUID válido.")
    return errors

# =============================
# 5. Generación y Validación OTP
# =============================

def generar_otp_sepa_transfer():
    """
    Genera un OTP para una transferencia SEPA usando el endpoint oficial.
    """
    url = "https://api.db.com/gw/dbapi/others/onetimepasswords/v2/single"
    payload = {
        "method": "PUSHTAN",
        "requestType": "SEPA_TRANSFER_GRANT",
        "requestData": {
            
            },
        "language": "es"
    }

    try:
        response = requests.post(url, json=payload, headers=HEADERS_DEFAULT, timeout=TIMEOUT_REQUEST)
        if response.status_code != 200:
            error_message = handle_error_response(response)
            registrar_log(payment_id=payload.get("paymentIdentification", {}).get("endToEndIdentification", "unknown"),
                          headers=HEADERS_DEFAULT, response_text=response.text, error=error_message)
            return {"error": error_message}
        data = response.json()
        otp_token = data.get('challengeProofToken')
        if not otp_token:
            raise Exception("OTP Token no recibido del banco.")
        return otp_token
    except Exception as e:
        registrar_log(payment_id=payload.get("paymentIdentification", {}).get("endToEndIdentification", "unknown"),
                      headers=HEADERS_DEFAULT, error=str(e))
        return {"error": str(e)}

def obtener_otp(session):
    """
    Obtiene OTP usando una sesión OAuth activa.
    """
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

    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest"
    })

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_REQUEST)
        if response.status_code != 201:
            error_message = handle_error_response(response)
            registrar_log(payment_id=payload.get("requestData", {}).get("paymentId", "unknown"),
                          headers=headers, response_text=response.text, error=error_message)
            return {"error": error_message}
        otp = response.json().get('challengeProofToken')
        return otp
    except Exception as e:
        registrar_log(payment_id=payload.get("requestData", {}).get("paymentId", "unknown"),
                      headers=headers, error=str(e))
        return {"error": str(e)}

def get_oauth_session(request=None):
    """
    Crea una sesión OAuth2 lista para usar con el token actual.
    """
    if not ACCESS_TOKEN:
        logger.error("ACCESS_TOKEN no configurado en el entorno")
        raise ValueError("ACCESS_TOKEN no configurado en variables de entorno.")

    return OAuth2Session(client_id=CLIENT_ID, token={"access_token": ACCESS_TOKEN, "token_type": "Bearer"})

# ===========================
# 6. Creación de PDFs de Transferencia
# ===========================

def generar_pdf_transferencia(transferencia):
    """
    Genera un PDF resumen de la transferencia SEPA.
    """
    creditor_name = transferencia.creditor.creditor_name.replace(" ", "_")
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
    current_y -= 50

    # Tabla Cabecera
    header_data = [
        ["Creation Date", datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
        ["Payment Reference", transferencia.payment_id]
    ]
    crear_tabla_pdf(c, header_data, current_y)
    current_y -= 100

    # Tabla Deudor
    debtor_data = [
        ["Debtor Information", ""],
        ["Name", transferencia.debtor.debtor_name],
        ["IBAN", transferencia.debtor_account.iban],
        ["Customer ID", transferencia.debtor.customer_id],
        ["Address", f"{transferencia.debtor.postal_address.street_and_house_number}, {transferencia.debtor.postal_address.zip_code_and_city}, {transferencia.debtor.postal_address.country}"]
    ]
    crear_tabla_pdf(c, debtor_data, current_y)
    current_y -= 140

    # Tabla Acreedor
    creditor_data = [
        ["Creditor Information", ""],
        ["Name", transferencia.creditor.creditor_name],
        ["IBAN", transferencia.creditor_account.iban],
        ["BIC", transferencia.creditor_agent.financial_institution_id],
        ["Address", f"{transferencia.creditor.postal_address.street_and_house_number}, {transferencia.creditor.postal_address.zip_code_and_city}, {transferencia.creditor.postal_address.country}"]
    ]
    crear_tabla_pdf(c, creditor_data, current_y)
    current_y -= 140

    # Tabla Transferencia
    transfer_data = [
        ["Transfer Details", ""],
        ["Amount", f"{transferencia.instructed_amount.amount} {transferencia.instructed_amount.currency}"],
        ["Requested Execution Date", transferencia.requested_execution_date.strftime('%d/%m/%Y')],
        ["Purpose Code", transferencia.purpose_code],
        ["Remittance Info Structured", transferencia.remittance_information_structured or 'N/A'],
        ["Remittance Info Unstructured", transferencia.remittance_information_unstructured or 'N/A'],
        ["Auth ID", transferencia.auth_id or 'N/A'],
        ["Transaction Status", transferencia.transaction_status],
        ["Priority", "High (Instant SEPA Credit Transfer)"]
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

# ===========================
# 7. Validaciones de Parámetros
# ===========================

def validate_parameters(data):
    """
    Validaciones manuales de campos básicos enviados en los payloads.
    """
    errors = []
    if 'iban' in data and not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$', data['iban']):
        errors.append("El IBAN proporcionado no es válido.")
    if 'requestedExecutionDate' in data:
        try:
            datetime.strptime(data['requestedExecutionDate'], '%Y-%m-%d')
        except ValueError:
            errors.append("El formato de 'requestedExecutionDate' debe ser yyyy-MM-dd.")
    if 'currency' in data and not re.match(r'^[A-Z]{3}$', data['currency']):
        errors.append("La moneda debe ser un código ISO 4217 válido (ejemplo: EUR).")
    if 'amount' in data and (not isinstance(data['amount'], (int, float)) or data['amount'] <= 0):
        errors.append("El monto debe ser un número positivo.")
    return errors

# ===========================
# 8. Validaciones de JSONSchema
# ===========================
# Definición de esquema JSON Schema para validación
def validate_schema(data, schema):
    """
    Valida un diccionario Python contra un esquema JSON Schema.
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        return False, str(e)

# Guardar pain.002 si el banco responde en XML
def guardar_pain002_si_aplica(response, payment_id):
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    content_type = response.headers.get("Content-Type", "")
    if "xml" in content_type and response.text:
        xml_response_path = os.path.join(carpeta, f"pain002_{payment_id}.xml")
        with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(response.text)
            
# ========================
# 9. Registro de Logs de Transferencias
# ========================

def registrar_log(payment_id, headers, response_text="", error=None):
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    log_path = os.path.join(carpeta, f"transferencia_{payment_id}.log")
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write("\n" + "=" * 80 + "\n")
        log.write(f"Fecha y hora: {datetime.now()}\n")
        log.write("=" * 80 + "\n")
        log.write("=== Headers enviados ===\n")
        log.write(json.dumps(headers, indent=4))
        log.write("\n\n")
        if error:
            log.write("=== Error ===\n")
            log.write(f"{error}\n")
        else:
            log.write("=== Respuesta ===\n")
            log.write(response_text)
        log.write("\n" + "=" * 80 + "\n")

def save_log(payment_id, request_headers, response_headers, response_text):
    """
    Guarda un log tradicional básico de request y response.
    """
    log_path = os.path.join(LOGS_DIR, f"transferencia_{payment_id}.log")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"--- Request Headers ---\n{json.dumps(request_headers, indent=2)}\n")
        f.write(f"\n--- Response Headers ---\n{json.dumps(dict(response_headers), indent=2)}\n")
        f.write(f"\n--- Response Text ---\n{response_text}\n")

def get_log_path(payment_id):
    return os.path.join(LOGS_DIR, f"transferencia_{payment_id}.log")

def log_exists(payment_id):
    """
    Verifica si ya existe un archivo de log para una transferencia.
    """
    return os.path.isfile(get_log_path(payment_id))

# ============================
# 10. Guardar respuesta XML pain.002
# ============================

def guardar_pain002_si_aplica(response, payment_id):
    """
    Guarda el archivo pain.002 (respuesta del banco en XML) si existe.
    """
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    content_type = response.headers.get("Content-Type", "")
    if "xml" in content_type and response.text:
        xml_response_path = os.path.join(carpeta, f"pain002_{payment_id}.xml")
        with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(response.text)

# =============================
# 11. Construcción de Payloads SEPA
# =============================

def preparar_payload_transferencia(transferencia, request=None):
    """
    Prepara el JSON que se enviará como body en la solicitud de transferencia SEPA.
    """
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

def construir_payload(transferencia: SepaCreditTransfer) -> dict:
    """
    Construye el payload para una transferencia SEPA usando objetos Django.
    """
    payload = preparar_payload_transferencia(transferencia)
    return payload

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