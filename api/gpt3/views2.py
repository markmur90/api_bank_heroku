import os
import uuid
import json
import requests
from datetime import datetime
from urllib import response
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views import View
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
from django.urls import reverse
from jsonschema import validate, ValidationError

from api.gpt3.bank_client import *
from api.gpt3.generate_aml import *
from api.gpt3.generate_xml import *
from api.gpt3.utils import *
from api.gpt3.helpers import *
from api.gpt3.models import *
from api.gpt3.forms import *

API_URL = "https://api.db.com:443/gw/dbapi/banking/transactions/v2"

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
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    })

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=(5, 15))
        if response.status_code == 201:
            otp = response.json().get('challengeProofToken')
            return otp
        else:
            return None
    except (RequestException, HTTPError, Timeout, ConnectionError):
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


@login_required
def crear_transferencia(request):
    if request.method == 'POST':
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            transferencia = form.save(commit=False)
            transferencia.payment_id = generate_payment_id_uuid()
            transferencia.auth_id = generate_payment_id_uuid()
            transferencia.transaction_status = "PDNG"

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

            try:
                generar_xml_pain001(transferencia, transferencia.payment_id)
                validar_xml_schema(transferencia.payment_id)
                generar_archivo_aml(transferencia, transferencia.payment_id)
            except Exception as e:
                registrar_log(transferencia.payment_id, {}, error=f"Error en generación inicial: {str(e)}")

            messages.success(request, "Transferencia creada correctamente.")
            return redirect('listar_transferenciasGPT3')
    else:
        form = SepaCreditTransferForm()
    return render(request, 'api/GPT3/crear_transferencia.html', {'form': form, 'transferencia': None})

@login_required
def listar_transferencias(request):
    transferencias = SepaCreditTransfer.objects.all().order_by('-created_at')
    paginator = Paginator(transferencias, 10)
    page = request.GET.get('page', 1)
    try:
        transferencias_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        transferencias_paginated = paginator.page(1)
    return render(request, 'api/GPT3/listar_transferencias.html', {'transferencias': transferencias_paginated})

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
                
    archivos = {
        'pain001': os.path.join(carpeta, f"pain001_{payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"pain001_{payment_id}.xml")) else None,
        'aml': os.path.join(carpeta, f"aml_{payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"aml_{payment_id}.xml")) else None,
        'pain002': os.path.join(carpeta, f"pain002_{payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"pain002_{payment_id}.xml")) else None,
    }

    return render(request, 'api/GPT3/detalle_transferencia.html', {
        'transferencia': transferencia,
        'log_files_content': log_files_content,
        'archivos': archivos
    })

@login_required
def descargar_pdf(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    try:
        generar_pdf_transferencia(transferencia)
        carpeta = obtener_ruta_schema_transferencia(payment_id)
        pdf_path = next(
            (os.path.join(carpeta, archivo) for archivo in os.listdir(carpeta)
             if archivo.endswith(".pdf") and payment_id in archivo),
            None
        )
        if not pdf_path or not os.path.exists(pdf_path):
            messages.error(request, "El archivo PDF no se encuentra disponible.")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)
        return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', as_attachment=True, filename=os.path.basename(pdf_path))
    except Exception as e:
        messages.error(request, f"Error al generar o descargar el PDF: {str(e)}")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

@login_required
def ver_log_transferencia(request, payment_id):
    log_path = get_log_path(payment_id)
    posibles_logs = [
        log_path,
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
        with open(log_encontrado, 'r', encoding='utf-8') as file:
            contenido = file.read()
        return HttpResponse(f"<pre>{contenido}</pre>", content_type="text/html")
    except Exception as e:
        messages.error(request, f"Error al visualizar el log: {str(e)}")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def enviar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    otp = obtener_otp(session)
    if not otp:
        messages.error(request, "No se pudo obtener el OTP para enviar la transferencia.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

    headers = HEADERS.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        "idempotency-id": payment_id,
        "otp": otp,
        "Content-Type": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    })

    payload = preparar_payload_transferencia(transferencia, request)

    try:
        generar_xml_pain001(transferencia, payment_id)
        validar_xml_schema(payment_id)
        generar_archivo_aml(transferencia, payment_id)

        response = requests.post(f"{API_URL}/", json=payload, headers=headers, timeout=(5, 15))

        registrar_log(payment_id, headers, response.text)

        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al enviar transferencia: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

        respuesta_json = response.json()
        transferencia.transaction_status = respuesta_json.get('transactionStatus', 'PDNG')
        transferencia.save()

        guardar_pain002_si_aplica(response, payment_id)

        messages.success(request, "Transferencia enviada correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        messages.error(request, f"Error interno al enviar: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def estado_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)

    headers = HEADERS.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    })

    try:
        response = requests.get(f"{API_URL}/{payment_id}/status", headers=headers, timeout=(5, 15))

        registrar_log(payment_id, headers, response.text)

        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al consultar estado: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

        respuesta_json = response.json()
        nueva_estado = respuesta_json.get("transactionStatus")
        if nueva_estado:
            transferencia.transaction_status = nueva_estado
            transferencia.save()

        guardar_pain002_si_aplica(response, payment_id)

        messages.success(request, "Estado actualizado correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        messages.error(request, f"Error interno al consultar estado: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

@csrf_exempt
@require_http_methods(["DELETE"])
@login_required
def cancelar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    otp = obtener_otp(session)
    if not otp:
        messages.error(request, "No se pudo obtener el OTP para cancelar la transferencia.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

    headers = HEADERS.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        "idempotency-id": payment_id,
        "otp": otp,
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    })

    try:
        response = requests.delete(f"{API_URL}/{payment_id}", headers=headers, timeout=(5, 15))

        registrar_log(payment_id, headers, response.text)

        if response.status_code not in [200, 201, 204]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al cancelar transferencia: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

        transferencia.transaction_status = "CANC"
        transferencia.save()

        messages.success(request, "Transferencia cancelada correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        messages.error(request, f"Error interno al cancelar: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

@csrf_exempt
@require_http_methods(["PATCH"])
@login_required
def retry_second_factor_view(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    otp = obtener_otp(session)
    if not otp:
        messages.error(request, "No se pudo obtener el OTP para reintentar segundo factor.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

    headers = HEADERS.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        "idempotency-id": payment_id,
        "otp": otp,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
        "Origin": "https://api.db.com",
        "X-Requested-With": "XMLHttpRequest"
    })

    payload = {
        "action": "CREATE",
        "authId": transferencia.auth_id
    }

    try:
        response = requests.patch(f"{API_URL}/{payment_id}", headers=headers, json=payload, timeout=(5, 15))

        registrar_log(payment_id, headers, response.text)

        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al reintentar autenticación: {mensaje}")
            return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

        guardar_pain002_si_aplica(response, payment_id)

        messages.success(request, "Reintento de autenticación completado correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        messages.error(request, f"Error interno al reintentar segundo factor: {str(e)}")
    return redirect('detalle_transferenciaGPT3', payment_id=payment_id)


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

            carpeta = obtener_ruta_schema_transferencia(bulk.payment_id)
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)

            with open(os.path.join(carpeta, f"pain001_bulk_{bulk.payment_id}.xml"), 'w', encoding='utf-8') as f:
                f.write(f"<BulkTransfer><PaymentID>{bulk.payment_id}</PaymentID></BulkTransfer>")

            with open(os.path.join(carpeta, f"aml_bulk_{bulk.payment_id}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"AML info for bulk transfer {bulk.payment_id}\n")

            messages.success(request, "Transferencia masiva creada correctamente.")
            return redirect('listar_transferenciasGPT3')

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

        try:
            with open(os.path.join(carpeta, f"pain001_bulk_{payment_id}.xml"), 'w', encoding='utf-8') as f:
                f.write(f"<BulkTransfer><PaymentID>{payment_id}</PaymentID><Status>Pending</Status></BulkTransfer>")

            with open(os.path.join(carpeta, f"aml_bulk_{payment_id}.txt"), 'w', encoding='utf-8') as f:
                f.write(f"AML actualizado para {payment_id}\n")

            respuesta_xml = f"<Response><Reference>{payment_id}</Reference><Status>Recibido</Status></Response>"
            with open(os.path.join(carpeta, f"pain002_bulk_{payment_id}.xml"), 'w', encoding='utf-8') as respuesta:
                respuesta.write(respuesta_xml)

            registrar_log(payment_id, {"Operacion": "Envio Bulk Simulado"}, respuesta_xml)

            bulk.transaction_status = "PDNG"
            bulk.save()

            messages.success(request, f"Transferencia masiva {payment_id} enviada y registrada.")
        except Exception as e:
            registrar_log(payment_id, {"Operacion": "Error Envio Bulk"}, error=str(e))
            messages.error(request, f"Error al enviar transferencia masiva: {str(e)}")

        return redirect('detalle_transferencia_bulkGPT3', payment_id=payment_id)

@login_required
class EstadoBulkTransferView(View):
    def get(self, request, payment_id):
        bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
        carpeta = obtener_ruta_schema_transferencia(payment_id)

        try:
            estado_xml = f"<StatusResponse><Reference>{payment_id}</Reference><Status>Procesando</Status></StatusResponse>"
            estado_path = os.path.join(carpeta, f"pain002_bulk_{payment_id}_estado.xml")
            with open(estado_path, 'w', encoding='utf-8') as xml:
                xml.write(estado_xml)

            registrar_log(payment_id, {"Operacion": "Consulta Estado Bulk Simulado"}, estado_xml)

            bulk.transaction_status = "ACSP"
            bulk.save()

            messages.success(request, f"Estado actualizado para la transferencia masiva {payment_id}.")
        except Exception as e:
            registrar_log(payment_id, {"Operacion": "Error Estado Bulk"}, error=str(e))
            messages.error(request, f"Error al consultar estado de transferencia masiva: {str(e)}")

        return redirect('detalle_transferencia_bulkGPT3', payment_id=payment_id)

@login_required
class DetalleBulkTransferView(View):
    def get(self, request, payment_id):
        bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
        carpeta = obtener_ruta_schema_transferencia(payment_id)
        log_path = get_log_path(payment_id)

        log_content = "Log no disponible"
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()

        archivos = {
            'pain001': os.path.join(carpeta, f"pain001_bulk_{payment_id}.xml"),
            'pain002': os.path.join(carpeta, f"pain002_bulk_{payment_id}.xml"),
            'estado': os.path.join(carpeta, f"pain002_bulk_{payment_id}_estado.xml"),
            'aml': os.path.join(carpeta, f"aml_bulk_{payment_id}.txt")
        }

        return render(request, 'api/GPT3/detalle_bulk.html', {
            'transferencia': bulk,
            'log': log_content,
            'archivos': archivos
        })


@login_required
def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cuenta creada correctamente.")
            return redirect('account_listGPT3')
    else:
        form = AccountForm()
    return render(request, 'api/GPT3/create_account.html', {'form': form})

@login_required
def create_amount(request):
    if request.method == 'POST':
        form = InstructedAmountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Monto creado correctamente.")
            return redirect('amount_listGPT3')
    else:
        form = InstructedAmountForm()
    return render(request, 'api/GPT3/create_amount.html', {'form': form})

@login_required
def create_financial_institution(request):
    if request.method == 'POST':
        form = FinancialInstitutionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Institución financiera creada correctamente.")
            return redirect('financial_institution_listGPT3')
    else:
        form = FinancialInstitutionForm()
    return render(request, 'api/GPT3/create_financial_institution.html', {'form': form})

@login_required
def create_postal_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Dirección postal creada correctamente.")
            return redirect('postal_address_listGPT3')
    else:
        form = AddressForm()
    return render(request, 'api/GPT3/create_postal_address.html', {'form': form})

@login_required
def create_payment_identification(request):
    if request.method == 'POST':
        form = PaymentIdentificationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Identificación de pago creada correctamente.")
            return redirect('listar_transferenciasGPT3')
    else:
        form = PaymentIdentificationForm()
    return render(request, 'api/GPT3/create_payment_identification.html', {'form': form})

@login_required
def create_debtor(request):
    if request.method == 'POST':
        form = DebtorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Deudor creado correctamente.")
            return redirect('debtor_listGPT3')
    else:
        form = DebtorForm()
    return render(request, 'api/GPT3/create_debtor.html', {'form': form})

@login_required
def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Acreedor creado correctamente.")
            return redirect('creditor_listGPT3')
    else:
        form = CreditorForm()
    return render(request, 'api/GPT3/create_creditor.html', {'form': form})

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