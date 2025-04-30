# api/gpt3/views2.py

import os
import uuid
import json
import requests
from datetime import datetime

from urllib import response
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views import View
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse

from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
from jsonschema import validate, ValidationError

from api.gpt3.generate_aml import generar_archivo_aml
from api.gpt3.generate_xml import generar_xml_pain001
from api.gpt3.helpers import (
    generate_deterministic_id,
    generate_payment_id,
    generate_payment_id_uuid,
    obtener_ruta_schema_transferencia
)
from api.gpt3.models import (
    Account, Address, BulkTransfer, Creditor, Debtor,
    FinancialInstitution, InstructedAmount, PaymentIdentification,
    SepaCreditTransfer
)
from api.gpt3.forms import (
    AccountForm, AddressForm, BulkTransferForm, CreditorForm, DebtorForm,
    FinancialInstitutionForm, GroupHeaderForm, InstructedAmountForm,
    PaymentIdentificationForm, PaymentInformationForm, SepaCreditTransferForm
)
from api.gpt3.schemas import sepa_credit_transfer_schema
from api.gpt3.utils import (
    HEADERS_DEFAULT,
    construir_payload,
    generar_otp_sepa_transfer,
    generar_pdf_transferencia,
    get_log_path,
    get_oauth_session,
    guardar_pain002_si_aplica,
    handle_error_response,
    obtener_otp,
    preparar_payload_transferencia,
    registrar_log,
    validate_schema
)

# Constantes de API
API_URL = "https://api.db.com:443/gw/dbapi/banking/transactions/v2"

# ===========================
# VISTAS DE TRANSFERENCIAS INDIVIDUALES
# ===========================

@login_required
def crear_transferencia(request):
    """
    Crea una nueva transferencia SEPA.
    """
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
                generar_archivo_aml(transferencia, transferencia.payment_id)
            except Exception as e:
                registrar_log(transferencia.payment_id, {}, error=f"Error generación inicial: {str(e)}")

            messages.success(request, "Transferencia creada correctamente.")
            return redirect('listar_transferenciasGPT3')
    else:
        form = SepaCreditTransferForm()
    
    return render(request, 'api/GPT3/crear_transferencia.html', {'form': form, 'transferencia': None})

@login_required
def listar_transferencias(request):
    """
    Lista todas las transferencias creadas, paginadas.
    """
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

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def enviar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    otp_token = generar_otp_sepa_transfer()

    if not otp_token:
        messages.error(request, "No se pudo obtener el OTP.")
        return redirect('listar_transferenciasGPT3')

    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        "idempotency-id": payment_id,
        "otp": otp_token,
        "x-request-id": str(uuid.uuid4()),
        "X-Requested-With": "XMLHttpRequest"
    })

    payload = preparar_payload_transferencia(transferencia, request)

    try:
        validate_schema(payload, sepa_credit_transfer_schema)
    except ValidationError as e:
        messages.error(request, f"Error de validación JSON: {str(e)}")
        return redirect('listar_transferenciasGPT3')

    try:
        response = requests.post(f"{API_URL}/", json=payload, headers=headers, timeout=(5, 15))
        registrar_log(payment_id, headers, response.text)

        if response.status_code not in [200, 201]:
            mensaje = handle_error_response(response)
            messages.error(request, f"Error al enviar transferencia: {mensaje}")
            transferencia.transaction_status = "ERRO"
            transferencia.save()
            return redirect('listar_transferenciasGPT3')

        respuesta_json = response.json()
        transferencia.transaction_status = respuesta_json.get('transactionStatus', 'PDNG')
        transferencia.save()

        guardar_pain002_si_aplica(response, payment_id)
        messages.success(request, "Transferencia enviada correctamente.")
    except Exception as e:
        registrar_log(payment_id, headers, "", error=str(e))
        transferencia.transaction_status = "ERROR"
        transferencia.save()
        messages.error(request, f"Error interno al enviar: {str(e)}")
    return redirect('listar_transferenciasGPT3')

# ===========================
# CONSULTAR ESTADO, CANCELAR Y RETRY 2FA
# ===========================

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def estado_transferencia(request, payment_id):
    """
    Consulta el estado de una transferencia en el banco.
    """
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)

    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
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
    """
    Cancela una transferencia enviada si aún es posible.
    """
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    otp = obtener_otp(session)

    if not otp:
        messages.error(request, "No se pudo obtener el OTP para cancelar.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        "idempotency-id": payment_id,
        "otp": otp,
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
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
    """
    Reintenta el segundo factor (OTP) en caso de fallo previo.
    """
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    otp_token = generar_otp_sepa_transfer()

    if not otp_token:
        messages.error(request, "No se pudo obtener OTP para reintentar.")
        return redirect('detalle_transferenciaGPT3', payment_id=payment_id)

    headers = HEADERS_DEFAULT.copy()
    headers.update({
        "Authorization": f"Bearer {session.token['access_token']}",
        "idempotency-id": payment_id,
        "otp": otp_token,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-request-id": str(uuid.uuid4()),
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

# ===========================
# VISTAS PARA TRANSFERENCIAS BULK
# ===========================

@login_required
class CrearBulkTransferView(View):
    """
    Vista para crear una transferencia masiva (bulk).
    """
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
            return redirect('listar_bulkGPT3')

        return render(request, 'api/GPT3/crear_bulk.html', {
            'bulk_form': bulk_form,
            'group_form': group_form,
            'payment_info_form': payment_info_form
        })

@login_required
class EnviarBulkTransferView(View):
    """
    Vista para simular el envío de una transferencia masiva.
    """
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
    """
    Vista para simular la consulta de estado de una transferencia masiva.
    """
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
    """
    Vista para mostrar los detalles de una transferencia masiva específica.
    """
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
def listar_bulk_transferencias(request):
    """
    Lista todas las transferencias masivas (bulk).
    """
    bulk_transfers = BulkTransfer.objects.all().order_by('-created_at')
    paginator = Paginator(bulk_transfers, 10)
    page = request.GET.get('page', 1)
    try:
        bulk_transfers_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        bulk_transfers_paginated = paginator.page(1)

    return render(request, 'api/GPT3/listar_bulk.html', {
        'bulk_transfers': bulk_transfers_paginated
    })


# ===========================
# VISTAS AUXILIARES: CREAR ENTIDADES
# ===========================

@login_required
def create_account(request):
    """
    Crea una nueva cuenta bancaria.
    """
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
    """
    Crea un monto (instrucción de cantidad).
    """
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
    """
    Crea una nueva institución financiera (banco).
    """
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
    """
    Crea una dirección postal.
    """
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
    """
    Crea identificación de pago (ID instrucción/endToEnd).
    """
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
    """
    Crea un deudor (ordenante).
    """
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
    """
    Crea un acreedor (beneficiario).
    """
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Acreedor creado correctamente.")
            return redirect('creditor_listGPT3')
    else:
        form = CreditorForm()
    return render(request, 'api/GPT3/create_creditor.html', {'form': form})

# ===========================
# VISTAS AUXILIARES: LISTAR ENTIDADES
# ===========================

@login_required
def postal_address_list_view(request):
    addresses = Address.objects.all().order_by('-id')
    paginator = Paginator(addresses, 10)
    page = request.GET.get('page', 1)
    try:
        addresses_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        addresses_paginated = paginator.page(1)
    return render(request, 'api/GPT3/postal_address_list.html', {'addresses': addresses_paginated})

@login_required
def debtor_list_view(request):
    debtors = Debtor.objects.all().order_by('-id')
    paginator = Paginator(debtors, 10)
    page = request.GET.get('page', 1)
    try:
        debtors_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        debtors_paginated = paginator.page(1)
    return render(request, 'api/GPT3/debtor_list.html', {'debtors': debtors_paginated})

@login_required
def creditor_list_view(request):
    creditors = Creditor.objects.all().order_by('-id')
    paginator = Paginator(creditors, 10)
    page = request.GET.get('page', 1)
    try:
        creditors_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        creditors_paginated = paginator.page(1)
    return render(request, 'api/GPT3/creditor_list.html', {'creditors': creditors_paginated})

@login_required
def account_list_view(request):
    accounts = Account.objects.all().order_by('-id')
    paginator = Paginator(accounts, 10)
    page = request.GET.get('page', 1)
    try:
        accounts_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        accounts_paginated = paginator.page(1)
    return render(request, 'api/GPT3/account_list.html', {'accounts': accounts_paginated})

@login_required
def financial_institution_list_view(request):
    institutions = FinancialInstitution.objects.all().order_by('-id')
    paginator = Paginator(institutions, 10)
    page = request.GET.get('page', 1)
    try:
        institutions_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        institutions_paginated = paginator.page(1)
    return render(request, 'api/GPT3/financial_institution_list.html', {'institutions': institutions_paginated})

@login_required
def amount_list_view(request):
    amounts = InstructedAmount.objects.all().order_by('-id')
    paginator = Paginator(amounts, 10)
    page = request.GET.get('page', 1)
    try:
        amounts_paginated = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        amounts_paginated = paginator.page(1)
    return render(request, 'api/GPT3/amount_list.html', {'amounts': amounts_paginated})

