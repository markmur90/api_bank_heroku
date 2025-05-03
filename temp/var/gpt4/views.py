import os
import json
import logging
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.contrib import messages
from jsonschema import validate, ValidationError
from .forms import TransferenciaForm
from .models import Transferencia
from .utils import generar_xml_transferencia, validar_xml
from .helpers import generar_codigo

logger = logging.getLogger(__name__)

HEADERS_ENVIO = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "es-CO",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
}

TIMEOUT_REQUEST = 10

with open(os.path.join(settings.BASE_DIR, 'schemas', 'sepaCreditTransferRequestSchema.json')) as f:
    TRANSFERENCIA_SCHEMA = json.load(f)

def enviar_transferencia(request):
    if request.method == 'POST':
        form = TransferenciaForm(request.POST)
        if form.is_valid():
            transferencia = form.save(commit=False)
            transferencia.payment_id = generar_codigo()
            transferencia.save()
            
            datos_transferencia = transferencia.to_dict()

            try:
                validate(instance=datos_transferencia, schema=TRANSFERENCIA_SCHEMA)
            except ValidationError as e:
                messages.error(request, f"Error de validación de datos: {e.message}")
                return redirect('gpt3:enviar_transferencia')

            try:
                otp = obtener_otp()
                headers = HEADERS_ENVIO.copy()
                headers.update({
                    "otp": otp,
                    "idempotency-id": transferencia.payment_id,
                })
                
                response = requests.post(
                    'https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer',
                    json=datos_transferencia,
                    headers=headers,
                    timeout=TIMEOUT_REQUEST
                )
                guardar_log(transferencia.payment_id, headers, response)

                if response.status_code == 201:
                    messages.success(request, "Transferencia enviada exitosamente.")
                    return redirect('gpt3:detalle_transferencia', pk=transferencia.pk)
                else:
                    messages.error(request, f"Error al enviar transferencia: {response.text}")
                    return redirect('gpt3:enviar_transferencia')

            except requests.Timeout:
                messages.error(request, "Timeout al conectar con el banco.")
            except requests.ConnectionError:
                messages.error(request, "Error de conexión.")
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
            return redirect('gpt3:enviar_transferencia')
    else:
        form = TransferenciaForm()
    return render(request, 'api/GPT3/enviar_transferencia.html', {'form': form})

def estado_transferencia(request, pk):
    transferencia = get_object_or_404(Transferencia, pk=pk)
    try:
        headers = HEADERS_ENVIO.copy()
        response = requests.get(
            f"https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{transferencia.payment_id}/status",
            headers=headers,
            timeout=TIMEOUT_REQUEST
        )
        guardar_log(transferencia.payment_id, headers, response)
        if response.status_code == 200:
            estado = response.json().get('transactionStatus', 'Desconocido')
            transferencia.estado = estado
            transferencia.save()
            messages.success(request, f"Estado actualizado: {estado}")
        else:
            messages.error(request, f"Error consultando estado: {response.text}")
    except requests.Timeout:
        messages.error(request, "Timeout al consultar estado.")
    except requests.ConnectionError:
        messages.error(request, "Error de conexión al consultar estado.")
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
    return redirect('gpt3:detalle_transferencia', pk=transferencia.pk)

def retry_second_factor_view(request, pk):
    transferencia = get_object_or_404(Transferencia, pk=pk)
    try:
        otp = obtener_otp()
        headers = HEADERS_ENVIO.copy()
        headers.update({
            "otp": otp,
            "idempotency-id": transferencia.payment_id,
        })
        payload = {
            "action": "CREATE",
            "authId": transferencia.auth_id
        }

        response = requests.patch(
            f"https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{transferencia.payment_id}",
            json=payload,
            headers=headers,
            timeout=TIMEOUT_REQUEST
        )
        guardar_log(transferencia.payment_id, headers, response)

        if response.status_code == 200:
            messages.success(request, "Segundo factor reintentado exitosamente.")
        else:
            messages.error(request, f"Error reintentando segundo factor: {response.text}")

    except requests.Timeout:
        messages.error(request, "Timeout al reintentar segundo factor.")
    except requests.ConnectionError:
        messages.error(request, "Error de conexión al reintentar segundo factor.")
    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")

    return redirect('gpt3:detalle_transferencia', pk=transferencia.pk)

def guardar_log(payment_id, headers, response):
    ruta_log = os.path.join(settings.BASE_DIR, f'logs/transferencias/transferencia_{payment_id}.log')
    os.makedirs(os.path.dirname(ruta_log), exist_ok=True)
    with open(ruta_log, 'w', encoding='utf-8') as f:
        f.write("\n==== HEADERS ENVIADOS ====\n")
        f.write(json.dumps(dict(headers), indent=4))
        f.write("\n==== HEADERS RESPUESTA ====\n")
        f.write(json.dumps(dict(response.headers), indent=4))
        f.write("\n==== BODY RESPUESTA ====\n")
        f.write(response.text)

def obtener_token():
    url = 'https://simulator-api.db.com:443/gw/oidc/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': settings.BANK_CLIENT_ID,
        'client_secret': settings.BANK_CLIENT_SECRET,
        'scope': 'sepa_credit_transfers'
    }
    response = requests.post(url, data=data, timeout=TIMEOUT_REQUEST)
    response.raise_for_status()
    return response.json()['access_token']

def obtener_otp():
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {obtener_token()}"
        }
        payload = {
            "method": "PUSHTAN",
            "requestType": "SEPA_TRANSFER_GRANT",
            "requestData": {}
        }
        response = requests.post(
            'https://simulator-api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges',
            json=payload,
            headers=headers,
            timeout=TIMEOUT_REQUEST
        )
        response.raise_for_status()
        resultado = response.json()
        return resultado['challengeProofToken']
    except Exception as e:
        raise Exception(f"Error obteniendo OTP: {str(e)}")
