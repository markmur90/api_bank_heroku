from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.http import FileResponse, HttpResponseBadRequest, JsonResponse
from .models import SepaCreditTransfer, ErrorResponse
from .utils import get_oauth_session
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import uuid
import re
import logging

logger = logging.getLogger(__name__)

ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
ORIGIN = 'https://api.db.com'

def validate_headers(headers):
    """Valida las cabeceras requeridas para las solicitudes."""
    errors = []
    required_headers = [
        'idempotency-id', 'otp', 'apikey', 'access-control-allow-origin',
        'access-control-allow-methods', 'access-control-allow-headers',
        'x-request-id', 'Accept-Encoding', 'Accept-Language', 'Connection',
        'Priority', 'Sec-Fetch-Dest', 'Sec-Fetch-Mode', 'Sec-Fetch-Site',
        'Sec-Fetch-User', 'Upgrade-Insecure-Requests', 'User-Agent'
    ]

    for header in required_headers:
        if header not in headers or not headers.get(header):
            errors.append(f"Cabecera '{header}' es requerida.")

    # Validar valores específicos
    if 'idempotency-id' in headers and not re.match(r'^[a-f0-9\-]{36}$', headers['idempotency-id']):
        errors.append("Cabecera 'idempotency-id' debe ser un UUID válido.")
    if 'x-request-id' in headers and not re.match(r'^[a-f0-9\-]{36}$', headers['x-request-id']):
        errors.append("Cabecera 'x-request-id' debe ser un UUID válido.")
    if headers.get('access-control-allow-origin') != '*':
        errors.append("Cabecera 'access-control-allow-origin' debe tener el valor '*'.")
    if headers.get('access-control-allow-methods') != 'GET, POST, PATCH, HEAD, OPTIONS, DELETE':
        errors.append("Cabecera 'access-control-allow-methods' tiene un valor inválido.")
    if headers.get('access-control-allow-headers') != 'idempotency-id, process-id, otp, Correlation-ID, Origin, Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers, Authorization, Cookie, X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security, previewsignature':
        errors.append("Cabecera 'access-control-allow-headers' tiene un valor inválido.")

    return errors


def handle_error_response(response):
    """Maneja los códigos de error específicos de la API."""
    error_messages = {
        401: "La función solicitada requiere un nivel de autenticación SCA.",
        404: "No se encontró el recurso solicitado.",
        409: "Conflicto: El recurso ya existe o no se puede procesar la solicitud."
    }
    error_code = response.status_code
    return error_messages.get(error_code, f"Error desconocido: {response.text}")


@require_http_methods(["POST"])
def cancel_sepa_transfer(request, payment_id):
    headers = {
        'idempotency-id': request.headers.get('idempotency-id'),
        'otp': request.headers.get('otp'),
        'Correlation-Id': request.headers.get('Correlation-Id'),
        'apikey': request.headers.get('apikey'),
        'process-id': request.headers.get('process-id'),
        'previewsignature': request.headers.get('previewsignature'),
        'Accept-Encoding': request.headers.get('Accept-Encoding'),
        'Accept-Language': request.headers.get('Accept-Language'),
        'Connection': request.headers.get('Connection'),
        'Priority': request.headers.get('Priority'),
        'Sec-Fetch-Dest': request.headers.get('Sec-Fetch-Dest'),
        'Sec-Fetch-Mode': request.headers.get('Sec-Fetch-Mode'),
        'Sec-Fetch-Site': request.headers.get('Sec-Fetch-Site'),
        'Sec-Fetch-User': request.headers.get('Sec-Fetch-User'),
        'Upgrade-Insecure-Requests': request.headers.get('Upgrade-Insecure-Requests'),
        'User-Agent': request.headers.get('User-Agent'),
    }
    validation_errors = validate_headers(headers)
    if validation_errors:
        return JsonResponse({'errors': validation_errors}, status=400)

    try:
        oauth = get_oauth_session(request)
        response = oauth.delete(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/{payment_id}',
            headers=headers
        )
        if response.status_code == 204:
            return JsonResponse({'message': 'Transferencia cancelada exitosamente.'}, status=204)
        else:
            error_message = handle_error_response(response)
            return JsonResponse({'error': error_message}, status=response.status_code)
    except Exception as e:
        logger.error(f"Error al cancelar transferencia: {str(e)}")
        return JsonResponse({'error': 'Error interno del servidor.'}, status=500)


def generate_transfer_pdf(request, payment_id):
    """Genera un PDF para una transferencia específica"""
    transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    pdf_path = generar_pdf_transferencia(transfer)
    response = FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', as_attachment=True, filename=f"{transfer.payment_id}.pdf")
    response['strict-transport-security'] = 'max-age=31536000; includeSubDomains; preload'
    response['x-content-type-options'] = 'nosniff'
    response['x-frame-options'] = 'DENY'
    response['x-request-id'] = request.headers.get('x-request-id', str(uuid.uuid4()))
    return response