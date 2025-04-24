import re
import uuid

# Constantes sensibles (idealmente cargar desde configuración o variables de entorno)
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...."  # Token de acceso JWT truncado
ORIGIN = "https://api.db.com"  # Dominio de origen esperado por la API externa

def validate_headers(headers):
    """
    Valida las cabeceras requeridas para las solicitudes SEPA.
    Retorna una lista de mensajes de error si alguna cabecera obligatoria falta 
    o no cumple el formato esperado.
    """
    errors = []
    idempotency_id = headers.get('idempotency-id', '')
    if not isinstance(idempotency_id, str):
        idempotency_id = str(idempotency_id)  # Normalizar a cadena
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

def build_headers(request, external_method):
    """
    Construye un diccionario de cabeceras base para la llamada a la API SEPA, 
    tomando los valores de la solicitud Django (`request`). El parámetro 
    `external_method` indica el método HTTP que usará la API externa 
    (por ejemplo: 'POST', 'GET', 'PATCH', 'DELETE').
    """
    method = external_method.upper()
    headers = {}
    # Cabecera idempotency-id
    if method in ['POST', 'GET']:
        # Generar nuevo UUID si no se proporciona (p. ej. iniciar transferencia o consultar estado)
        headers['idempotency-id'] = request.headers.get('idempotency-id', str(uuid.uuid4()))
    else:
        # Requerir el idempotency-id proporcionado (p. ej. cancelación o segundo factor)
        headers['idempotency-id'] = request.headers.get('idempotency-id')
    # Cabecera OTP
    if method == 'POST':
        # En iniciar transferencia, usar OTP del formulario o valor por defecto para generar desafío
        headers['otp'] = request.POST.get('otp', 'SEPA_TRANSFER_GRANT')
    elif method in ['PATCH', 'DELETE']:
        # En cancelación o segundo factor, tomar OTP de los encabezados de la petición
        headers['otp'] = request.headers.get('otp')
    # (Para 'GET', la cabecera OTP no se incluye ya que no se requiere segundo factor en consulta de estado)
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
    """
    Agrega cabeceras comunes a la petición API, como autenticación y tipo de contenido,
    según el método HTTP externo especificado.
    """
    # Autenticación con token Bearer
    headers['Authorization'] = f"Bearer {ACCESS_TOKEN}"
    # Aceptación de respuesta JSON en todos los casos
    headers['Accept'] = 'application/json'
    # En métodos con cuerpo (POST/PATCH), especificar el tipo de contenido JSON
    if external_method.upper() in ['POST', 'PATCH']:
        headers['Content-Type'] = 'application/json'
    return headers
