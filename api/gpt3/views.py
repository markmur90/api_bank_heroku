import uuid
import os
import requests
from datetime import datetime
from urllib import response
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views import View
import xml.etree.ElementTree as ET
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
from django.urls import reverse

from api.gpt3.bank_client import *
from api.gpt3.generate_aml import *
from api.gpt3.generate_xml import *
from api.gpt3.models import *
from api.gpt3.forms import *
from api.gpt3.utils import *
from api.gpt3.helpers import *

# API_URL = "https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"
API_URL = "https://api.db.com:443/gw/dbapi/banking/transactions/v2"
# API_URL = "https://127.0.0.1:2222"


HEADERS = {
    "Accept": "application/json",
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
    "X-Content-Type-Options": "nosniff"
}

def obtener_otp():
    url = "https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges"
    payload = {
        "method": "PUSHTAN",
        "requestType": "SEPA_TRANSFER_GRANT",
        "requestData": {}
    }
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        if response.status_code == 201:
            otp = response.json().get('challengeProofToken')
            return otp
        else:
            logger.error(f"Error OTP - Código: {response.status_code}, Mensaje: {response.text}")
            return None
    except requests.exceptions.Timeout:
        logger.error("Timeout al solicitar OTP.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión solicitando OTP: {str(e)}")
        return None


@login_required
def descargar_pdf(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    generar_pdf_transferencia(transferencia)
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)

    pdf_archivo = next(
        (os.path.join(carpeta_transferencia, f) for f in os.listdir(carpeta_transferencia)
         if f.endswith(".pdf") and payment_id in f),
        None
    )

    if not pdf_archivo or not os.path.exists(pdf_archivo):
        messages.error(request, "El archivo PDF no se encuentra disponible.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

    return FileResponse(open(pdf_archivo, 'rb'), content_type='application/pdf', as_attachment=True, filename=os.path.basename(pdf_archivo))


# Función para registrar logs
def registrar_log(payment_id, headers, response_text, error=None):
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)

    log_path = os.path.join(carpeta_transferencia, f"transferencia_{payment_id}.log")
    with open(log_path, 'a', encoding='utf-8') as log_file:
        # Separador inicial
        log_file.write("\n" + "=" * 80 + "\n")
        log_file.write(f"Registro de transferencia - Payment ID: {payment_id}\n")
        log_file.write(f"Fecha y hora: {datetime.now()}\n")
        log_file.write("=" * 80 + "\n\n")

        # Headers enviados
        log_file.write("=== Headers enviados ===\n")
        for key, value in headers.items():
            log_file.write(f"{key}: {value}\n")
        log_file.write("\n")

        # Respuesta o error
        if error:
            log_file.write("=== Error ===\n")
            log_file.write(f"{error}\n")
        else:
            log_file.write("=== Respuesta ===\n")
            log_file.write(f"{response_text}\n")

        # Separador final
        log_file.write("\n" + "=" * 80 + "\n")
        log_file.write("Fin del registro\n")
        log_file.write("=" * 80 + "\n\n")




@login_required
def ver_log_transferencia(request, payment_id):
    # Ruta del log principal de la transferencia
    log_path = get_log_path(payment_id)

    # En caso que el log de la transferencia no exista, buscamos errores
    posibles_logs = [
        log_path,  # transferencia_<payment_id>.log
        os.path.join(os.path.dirname(log_path), f"error_cancelar_{payment_id}.log"),
        os.path.join(os.path.dirname(log_path), f"error_estado_{payment_id}.log"),
        os.path.join(os.path.dirname(log_path), f"error_{payment_id}.log"),
    ]

    log_encontrado = None
    for path in posibles_logs:
        if os.path.exists(path):
            log_encontrado = path
            break

    if not log_encontrado:
        messages.error(request, "Log no disponible para esta transferencia.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

    try:
        with open(log_encontrado, 'r', encoding='utf-8') as log_file:
            contenido = log_file.read()

        response = HttpResponse(f"<pre>{contenido}</pre>", content_type="text/html")
        response['Content-Disposition'] = f'inline; filename=\"{os.path.basename(log_encontrado)}\"'
        return response

    except Exception as e:
        messages.error(request, f"Error al visualizar el log: {str(e)}")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)



# Crear Transferencia

@login_required
def crear_transferencia(request):
    if request.method == 'POST':
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            transferencia = form.save(commit=False)
            transferencia.payment_id = generate_payment_id_uuid()
            transferencia.auth_id = generate_payment_id_uuid()
            transferencia.transaction_status = "PDNG"

            # Crear y asignar PaymentIdentification
            payment_identification = PaymentIdentification.objects.create(
                instruction_id=generate_deterministic_id(
                    transferencia.payment_id,
                    transferencia.creditor_account.iban,
                    transferencia.instructed_amount.amount
                ),
                end_to_end_id=generate_deterministic_id(
                    transferencia.debtor_account.iban,
                    transferencia.creditor_account.iban,
                    transferencia.instructed_amount.amount,
                    transferencia.requested_execution_date,
                    prefix="E2E"
                )
            )
            transferencia.payment_identification = payment_identification

            transferencia.save()
            # Guardar archivos directamente al crear (pain.001 + AML)
            generar_xml_pain001(transferencia, transferencia.payment_id)
            generar_archivo_aml(transferencia, transferencia.payment_id)

            messages.success(request, "Transferencia creada correctamente.")
            return redirect('dashboard')  # Sin argumentos
    else:
        form = SepaCreditTransferForm()
    return render(request, 'api/GPT3/crear_transferencia.html', {'form': form, 'transferencia': None})


@login_required
def listar_transferencias(request):
    transferencias = SepaCreditTransfer.objects.all().order_by('created_at')
    return render(request, 'api/GPT3/listar_transferencias.html', {'transferencias': transferencias})


@login_required
def detalle_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

    carpeta = obtener_ruta_schema_transferencia(payment_id)
    archivos_logs = {
        archivo: os.path.join(carpeta, archivo)
        for archivo in os.listdir(carpeta)
        if archivo.endswith(".log")
    }

    log_files_content = {}
    for nombre, ruta in archivos_logs.items():
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                log_files_content[nombre] = f.read()

    xml_pain001 = os.path.join(carpeta, f"pain001_{payment_id}.xml")
    xml_pain002 = os.path.join(carpeta, f"pain002_{payment_id}.xml")
    aml_file = os.path.join(carpeta, f"aml_{payment_id}.xml")

    archivos = {
        'pain001': xml_pain001 if os.path.exists(xml_pain001) else None,
        'aml': aml_file if os.path.exists(aml_file) else None,
        'pain002': xml_pain002 if os.path.exists(xml_pain002) else None,
        
    }

    return render(request, 'api/GPT3/detalle_transferencia.html', {
        'transferencia': transferencia,
        'log_files_content': log_files_content,  # Todos los logs con su contenido
        'archivos': archivos
    })


# Enviar transferencia
@csrf_exempt
@require_http_methods(["POST"])
def enviar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    otp = request.POST.get('otp', '3H76IHBSDB56')  # Capturar OTP del formulario o usar un valor predeterminado
    session = get_oauth_session(request)
    access_token = session.token['access_token']

    # Capturamos los datos adicionales de PaymentTypeInformation
    service_level_code = request.POST.get('payment_type_information_service_level', 'INST')
    local_instrument_code = request.POST.get('payment_type_information_local_instrument', 'INST')
    category_purpose_code = request.POST.get('payment_type_information_category_purpose', 'GDSV')

    headers = {
        "Authorization": f"Bearer {access_token}",
        "idempotency-id": payment_id,
        "otp": otp,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
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
                "serviceLevelCode": service_level_code
            },
            "localInstrument": {
                "localInstrumentCode": local_instrument_code
            },
            "categoryPurpose": {
                "categoryPurposeCode": category_purpose_code
            }
        }
    }

    try:
        # Generar y validar el archivo XML (pain.001)
        generar_xml_pain001(transferencia, payment_id)
        carpeta_xml = obtener_ruta_schema_transferencia(payment_id)
        pain001_path = os.path.join(carpeta_xml, f"pain001_{payment_id}.xml")
        if os.path.exists(pain001_path):
            with open(pain001_path, 'r', encoding='utf-8') as f:
                validate_pain001(f.read())

        # Generar el archivo AML
        generar_archivo_aml(transferencia, payment_id)

        # Enviar la solicitud al banco
        response = requests.post(f"{API_URL}/", json=payload, headers=headers, timeout=(5, 15))

        carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
        log_path = os.path.join(carpeta_transferencia, f"error_enviar_{payment_id}.log")
        with open(log_path, 'w') as log_file:
            log_file.write(f"Headers enviados:\n{headers}\n\n")
            log_file.write(f"Headers respuesta:\n{dict(response.headers)}\n\n")
            log_file.write(f"Body:\n{response.text}\n")
        
        # Verificar el código de estado de la respuesta
        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al enviar transferencia: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

        response.raise_for_status()

        # Guardar respuesta XML pain.002 si es proporcionada
        content_type = response.headers.get("Content-Type", "")
        if "xml" in content_type:
            xml_response_path = os.path.join(carpeta_xml, f"pain002_{payment_id}.xml")
            with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
                xmlfile.write(response.text)

        # Actualizar el estado de la transferencia
        transferencia.transaction_status = response.json().get("transactionStatus", "PDNG")
        transferencia.save()

        # Registrar logs
        registrar_log(payment_id, headers, response.text)
        messages.success(request, "Transferencia enviada exitosamente.")

    except requests.RequestException as e:
        # Registrar errores en el log
        registrar_log(payment_id, headers, "", error=str(e))

        carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
        error_log_path = os.path.join(carpeta_transferencia, f"error_enviar_{payment_id}.log")
        with open(error_log_path, 'w', encoding='utf-8') as error_file:
            error_file.write(f"Error al enviar transferencia: {str(e)}\n")

        messages.error(request, f"Error al enviar transferencia: {str(e)}")

    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)




# Estado de transferencia
@csrf_exempt
@require_http_methods(["GET"])
def estado_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    access_token = session.token['access_token']

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.get(f"{API_URL}/{payment_id}/status", headers=headers, timeout=(5, 15))


        carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
        log_path = os.path.join(carpeta_transferencia, f"error_estado_{payment_id}.log")
        with open(log_path, 'w') as log_file:
            log_file.write(f"Headers enviados:\n{headers}\n\n")
            log_file.write(f"Headers respuesta:\n{dict(response.headers)}\n\n")
            log_file.write(f"Body:\n{response.text}\n")

        # Verificar el código de estado de la respuesta
        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al enviar transferencia: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
        
        response.raise_for_status()
        
        # Guardar respuesta XML pain.002 si es proporcionada
        carpeta_xml = obtener_ruta_schema_transferencia(payment_id)
        content_type = response.headers.get("Content-Type", "")
        if "xml" in content_type:
            xml_response_path = os.path.join(carpeta_xml, f"pain002_{payment_id}.xml")
            with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
                xmlfile.write(response.text)
                
        nueva_estado = response.json().get("transactionStatus")
        
        if nueva_estado:
            transferencia.transaction_status = nueva_estado
            transferencia.save()
        registrar_log(payment_id, headers, response.text)
        messages.success(request, "Estado actualizado correctamente.")
    except requests.RequestException as e:
        registrar_log(payment_id, headers, "", error=str(e))
        
        carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
        error_log_path = os.path.join(carpeta_transferencia, f"error_estado_{payment_id}.log")
        with open(error_log_path, 'w', encoding='utf-8') as error_file:
            error_file.write(f"Error al enviar transferencia: {str(e)}\n")        
        
        messages.error(request, f"Error al consultar estado: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)


# Cancelar transferencia
@csrf_exempt
@require_http_methods(["DELETE"])
def cancelar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    access_token = session.token['access_token']
    otp = request.POST.get('otp', '3H76IHBSDB56')

    headers = {
        "Authorization": f"Bearer {access_token}",
        "idempotency-id": payment_id,
        "otp": otp,
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.delete(f"{API_URL}/{payment_id}", headers=headers, timeout=(5, 15))
        response.raise_for_status()
        transferencia.transaction_status = "CANC"
        transferencia.save()
        registrar_log(payment_id, headers, response.text)
        messages.success(request, "Transferencia cancelada exitosamente.")
    except requests.RequestException as e:
        registrar_log(payment_id, headers, "", error=str(e))
        
        carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
        error_log_path = os.path.join(carpeta_transferencia, f"error_cancelar_{payment_id}.log")
        with open(error_log_path, 'w', encoding='utf-8') as error_file:
            error_file.write(f"Error al enviar transferencia: {str(e)}\n")        
        
        messages.error(request, f"Error al cancelar transferencia: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)





# Reintentar segundo factor
@csrf_exempt
@require_http_methods(["PATCH"])
def retry_second_factor_view(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    access_token = session.token['access_token']
    otp = request.POST.get('otp', '3H76IHBSDB56')

    payload = {
        "action": request.POST.get("action", "CREATE"),
        "authId": transferencia.auth_id
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "idempotency-id": payment_id,
        "otp": otp,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = requests.patch(f"{API_URL}/{payment_id}", json=payload, headers=headers, timeout=(5, 15))
        response.raise_for_status()
        
        # Guardar respuesta XML pain.002 si es proporcionada
        carpeta_xml = obtener_ruta_schema_transferencia(payment_id)        
        content_type = response.headers.get("Content-Type", "")
        if "xml" in content_type:
            xml_response_path = os.path.join(carpeta_xml, f"pain002_{payment_id}.xml")
            with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
                xmlfile.write(response.text)
        
        registrar_log(payment_id, headers, response.text)
        messages.success(request, "Reintento de segundo factor realizado correctamente.")
        
        carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
        log_path = os.path.join(carpeta_transferencia, f"error_2FA_{payment_id}.log")
        with open(log_path, 'w') as log_file:
            log_file.write(f"Headers enviados:\n{headers}\n\n")
            log_file.write(f"Headers respuesta:\n{dict(response.headers)}\n\n")
            log_file.write(f"Body:\n{response.text}\n")        
        
    except requests.RequestException as e:
        registrar_log(payment_id, headers, "", error=str(e))
        
        carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)
        error_log_path = os.path.join(carpeta_transferencia, f"error_2FA_{payment_id}.log")
        with open(error_log_path, 'w', encoding='utf-8') as error_file:
            error_file.write(f"Error al enviar transferencia: {str(e)}\n")        
        
        messages.error(request, f"Error al reintentar autenticación: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)




# Crear Transferencia Masiva
@login_required
class CrearBulkTransferView(View):
    def get(self, request):
        bulk_form = BulkTransferForm()
        group_form = GroupHeaderForm()
        payment_info_form = PaymentInformationForm()
        return render(request, 'api/GPT3/crear_bulk.html', {
            'bulk_form': bulk_form,
            'group_form': group_form,
            'payment_info_form': payment_info_form
        })

    def post(self, request):
        bulk_form = BulkTransferForm(request.POST)
        group_form = GroupHeaderForm(request.POST)
        payment_info_form = PaymentInformationForm(request.POST)
        if all([bulk_form.is_valid(), group_form.is_valid(), payment_info_form.is_valid()]):
            group = group_form.save()
            bulk = bulk_form.save(commit=False)
            bulk.payment_id = generate_payment_id(prefix="BLK")
            bulk.group_header = group
            bulk.save()

            info = payment_info_form.save(commit=False)
            info.bulk = bulk
            info.payment_information_id = generate_deterministic_id(
                bulk.payment_id, info.control_sum, info.requested_execution_date
            )
            info.save()

            # Crear estructura de archivos asociada
            carpeta = obtener_ruta_schema_transferencia(bulk.payment_id)
            with open(os.path.join(carpeta, f"pain001_bulk_{bulk.payment_id}.xml"), 'w', encoding='utf-8') as f:
                f.write(f"<BulkTransfer><PaymentID>{bulk.payment_id}</PaymentID></BulkTransfer>")
            with open(os.path.join(carpeta, f"aml_bulk_{bulk.payment_id}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"Bulk AML info for {bulk.payment_id}\n")

            messages.success(request, "Transferencia masiva creada y archivos generados.")
            return redirect('dashboard')

        return render(request, 'api/GPT3/crear_bulk.html', {
            'bulk_form': bulk_form,
            'group_form': group_form,
            'payment_info_form': payment_info_form
        })


@login_required
class EnviarBulkTransferView(View):
    def get(self, request, payment_id):
        bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
        carpeta = obtener_ruta_schema_transferencia(payment_id)
        log_path = obtener_ruta_log_transferencia(payment_id)

        try:
            # Regenerar XML y AML de prueba para bulk
            with open(os.path.join(carpeta, f"pain001_bulk_{payment_id}.xml"), 'w', encoding='utf-8') as f:
                f.write(f"<BulkTransfer><PaymentID>{payment_id}</PaymentID><Status>Pending</Status></BulkTransfer>")
            with open(os.path.join(carpeta, f"aml_bulk_{payment_id}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"AML info actualizada para {payment_id}\n")

            # Simular respuesta del banco
            respuesta_xml = f"<Response><Reference>{payment_id}</Reference><Status>Recibido</Status></Response>"
            with open(os.path.join(carpeta, f"pain002_bulk_{payment_id}.xml"), 'w', encoding='utf-8') as respuesta:
                respuesta.write(respuesta_xml)

            with open(log_path, 'a') as log:
                log.write(f"\nEnvio bulk - {datetime.now()}\nPayload generado y respuesta simulada:\n{respuesta_xml}\n")

            bulk.transaction_status = "PDNG"
            bulk.save()
            messages.success(request, f"Transferencia masiva {payment_id} enviada y registrada.")

        except Exception as e:
            messages.error(request, f"Error al simular envío masivo: {str(e)}")

        return redirect('detalle_transferencia_bulkGPT3', payment_id=payment_id)


@login_required
class EstadoBulkTransferView(View):
    def get(self, request, payment_id):
        bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
        log_path = obtener_ruta_log_transferencia(payment_id)
        carpeta = obtener_ruta_schema_transferencia(payment_id)

        try:
            # Simular consulta de estado y respuesta del banco
            estado_xml = f"<StatusResponse><Reference>{payment_id}</Reference><Status>Procesando</Status></StatusResponse>"
            estado_path = os.path.join(carpeta, f"pain002_bulk_{payment_id}_estado.xml")
            with open(estado_path, 'w', encoding='utf-8') as xml:
                xml.write(estado_xml)

            with open(log_path, 'a') as log:
                log.write(f"\nConsulta estado bulk - {datetime.now()}\nHeaders: Simulados\n\nRespuesta:\n{estado_xml}\n")

            bulk.transaction_status = "ACSP"
            bulk.save()
            messages.success(request, f"Estado actualizado para la transferencia masiva {payment_id}.")

        except Exception as e:
            messages.error(request, f"Error al consultar estado de la transferencia masiva: {str(e)}")

        return redirect('detalle_transferencia_bulkGPT3', payment_id=payment_id)


@login_required
class DetalleBulkTransferView(View):
    def get(self, request, payment_id):
        bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
        log_path = obtener_ruta_log_transferencia(payment_id)
        log_content = "Log no disponible"
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_content = f.read()

        carpeta = obtener_ruta_schema_transferencia(payment_id)
        xml_pain001 = os.path.join(carpeta, f"pain001_bulk_{payment_id}.xml")
        xml_pain002 = os.path.join(carpeta, f"pain002_bulk_{payment_id}.xml")
        xml_estado = os.path.join(carpeta, f"pain002_bulk_{payment_id}_estado.xml")
        aml_file = os.path.join(carpeta, f"aml_bulk_{payment_id}.txt")

        archivos = {
            'pain001': xml_pain001 if os.path.exists(xml_pain001) else None,
            'pain002': xml_pain002 if os.path.exists(xml_pain002) else None,
            'estado': xml_estado if os.path.exists(xml_estado) else None,
            'aml': aml_file if os.path.exists(aml_file) else None
        }

        return render(request, 'api/GPT3/detalle_bulk.html', {
            'transferencia': bulk,
            'log': log_content,
            'archivos': archivos
        })








# Listar vistas

def postal_address_list_view(request):
    addresses = Address.objects.all().order_by('-id')
    paginator = Paginator(addresses, 10)
    page = request.GET.get('page', 1)
    try:
        addresses_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        addresses_paginated = paginator.page(1)
    return render(request, 'api/GPT3/postal_address_list.html', {'addresses': addresses_paginated})


def debtor_list_view(request):
    debtors = Debtor.objects.all().order_by('-id')
    paginator = Paginator(debtors, 10)
    page = request.GET.get('page', 1)
    try:
        debtors_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        debtors_paginated = paginator.page(1)
    return render(request, 'api/GPT3/debtor_list.html', {'debtors': debtors_paginated})


def creditor_list_view(request):
    creditors = Creditor.objects.all().order_by('-id')
    paginator = Paginator(creditors, 10)
    page = request.GET.get('page', 1)
    try:
        creditors_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        creditors_paginated = paginator.page(1)
    return render(request, 'api/GPT3/creditor_list.html', {'creditors': creditors_paginated})


def account_list_view(request):
    accounts = Account.objects.all().order_by('-id')
    paginator = Paginator(accounts, 10)
    page = request.GET.get('page', 1)
    try:
        accounts_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        accounts_paginated = paginator.page(1)
    return render(request, 'api/GPT3/account_list.html', {'accounts': accounts_paginated})


def financial_institution_list_view(request):
    institutions = FinancialInstitution.objects.all().order_by('-id')
    paginator = Paginator(institutions, 10)
    page = request.GET.get('page', 1)
    try:
        institutions_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        institutions_paginated = paginator.page(1)
    return render(request, 'api/GPT3/financial_institution_list.html', {'institutions': institutions_paginated})


def amount_list_view(request):
    amounts = InstructedAmount.objects.all().order_by('-id')
    paginator = Paginator(amounts, 10)
    page = request.GET.get('page', 1)
    try:
        amounts_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        amounts_paginated = paginator.page(1)
    return render(request, 'api/GPT3/amount_list.html', {'amounts': amounts_paginated})




# Crear

def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('account_listGPT3')
    else:
        form = AccountForm()
    return render(request, 'api/GPT3/create_account.html', {'form': form})


def create_amount(request):
    if request.method == 'POST':
        form = InstructedAmountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('amount_listGPT3')
    else:
        form = InstructedAmountForm()
    return render(request, 'api/GPT3/create_amount.html', {'form': form})


def create_financial_institution(request):
    if request.method == 'POST':
        form = FinancialInstitutionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('financial_institution_listGPT3')
    else:
        form = FinancialInstitutionForm()
    return render(request, 'api/GPT3/create_financial_institution.html', {'form': form})


def create_postal_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('postal_address_listGPT3')
    else:
        form = AddressForm()
    return render(request, 'api/GPT3/create_postal_address.html', {'form': form})


def create_payment_identification(request):
    if request.method == 'POST':
        form = PaymentIdentificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transferGPT3')
    else:
        form = PaymentIdentificationForm()
    return render(request, 'api/GPT3/create_payment_identification.html', {'form': form})


def create_debtor(request):
    if request.method == 'POST':
        form = DebtorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('debtor_listGPT3')
    else:
        form = DebtorForm()
    return render(request, 'api/GPT3/create_debtor.html', {'form': form})


def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('creditor_listGPT3')
    else:
        form = CreditorForm()
    return render(request, 'api/GPT3/create_creditor.html', {'form': form})


