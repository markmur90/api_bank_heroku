import os
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views import View

from .models import *
from .forms import *
from .utils import (
    get_oauth_session, build_headers, attach_common_headers,
    validate_headers, handle_error_response, generate_transfer_pdf
)
from .helpers import generate_payment_id

LOG_DIR = os.path.join("logs", "transferencias")
SCHEMA_DIR = os.path.join("schemas")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SCHEMA_DIR, exist_ok=True)

# Vistas SEPA individuales

@login_required
def crear_transferencia(request):
    if request.method == 'POST':
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            transferencia = form.save(commit=False)
            transferencia.payment_id = generate_payment_id("PMT")
            transferencia.save()
            messages.success(request, "Transferencia creada.")
            return redirect('listar_transferencias')
    else:
        form = SepaCreditTransferForm()
    return render(request, 'sepa_transferencias/crear_transferencia.html', {'form': form})

@login_required
def listar_transferencias(request):
    transferencias = SepaCreditTransfer.objects.all().order_by('-created_at')
    return render(request, 'sepa_transferencias/listar_transferencias.html', {'transferencias': transferencias})

@login_required
def detalle_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    log_path = os.path.join(LOG_DIR, f"transferencia_{payment_id}.log")
    log_content = "Log no disponible"
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log_content = f.read()
    return render(request, 'sepa_transferencias/detalle_transferencia.html', {
        'transferencia': transferencia,
        'log': log_content
    })

@login_required
def enviar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    headers = build_headers(request, 'POST')
    attach_common_headers(headers, 'POST')
    errores = validate_headers(headers)
    if errores:
        messages.error(request, "Errores en cabeceras: " + ", ".join(errores))
        return redirect('detalle_transferencia', payment_id=payment_id)

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
        "paymentIdentification": {
            "endToEndIdentification": transferencia.payment_identification.end_to_end_id,
            "instructionId": transferencia.payment_identification.instruction_id
        },
        "instructedAmount": {
            "amount": float(transferencia.instructed_amount.amount),
            "currency": transferencia.instructed_amount.currency
        },
        "purposeCode": transferencia.purpose_code,
        "remittanceInformationStructured": transferencia.remittance_information_structured,
        "remittanceInformationUnstructured": transferencia.remittance_information_unstructured,
        "requestedExecutionDate": transferencia.requested_execution_date.strftime('%Y-%m-%d')
    }

    try:
        res = session.post(
            'https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/',
            json=payload, headers=headers
        )
        log_path = os.path.join(LOG_DIR, f"transferencia_{payment_id}.log")
        with open(log_path, 'w') as log_file:
            log_file.write(f"Headers enviados:\n{headers}\n\n")
            log_file.write(f"Headers respuesta:\n{dict(res.headers)}\n\n")
            log_file.write(f"Body:\n{res.text}\n")

        if res.status_code not in [200, 201]:
            mensaje = handle_error_response(res)
            messages.error(request, f"Error al enviar transferencia: {mensaje}")
            return redirect('detalle_transferencia', payment_id=payment_id)

        transferencia.transaction_status = "PDNG"
        transferencia.save()
        messages.success(request, "Transferencia enviada correctamente.")
        return redirect('detalle_transferencia', payment_id=payment_id)

    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect('detalle_transferencia', payment_id=payment_id)

@login_required
def estado_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    headers = build_headers(request, 'GET')
    attach_common_headers(headers, 'GET')
    url = f"https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{payment_id}/status"
    res = session.get(url, headers=headers)
    log_path = os.path.join(LOG_DIR, f"transferencia_{payment_id}.log")
    with open(log_path, 'a') as log_file:
        log_file.write(f"\nConsulta de estado - {datetime.now()}\nHeaders:\n{headers}\n\nRespuesta:\n{res.text}\n")

    if res.status_code == 200:
        transferencia.transaction_status = res.json().get("transactionStatus", transferencia.transaction_status)
        transferencia.save()
        messages.success(request, "Estado actualizado desde el banco.")
    else:
        mensaje = handle_error_response(res)
        messages.error(request, f"Error al consultar estado: {mensaje}")

    return redirect('detalle_transferencia', payment_id=payment_id)

@login_required
def descargar_pdf(request, payment_id):
    return generate_transfer_pdf(request, payment_id)

# Vistas para transferencias masivas (crear, enviar, estado, detalle) también incluidas en el proyecto
class CrearBulkTransferView(View):
    def get(self, request):
        bulk_form = BulkTransferForm()
        group_form = GroupHeaderForm()
        payment_info_form = PaymentInformationForm()
        return render(request, 'sepa_transferencias/crear_bulk.html', {
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
            bulk.group_header = group
            bulk.save()
            info = payment_info_form.save(commit=False)
            info.bulk = bulk
            info.save()
            messages.success(request, "Transferencia masiva creada.")
            return redirect('listar_transferencias')
        return render(request, 'sepa_transferencias/crear_bulk.html', {
            'bulk_form': bulk_form,
            'group_form': group_form,
            'payment_info_form': payment_info_form
        })

class EnviarBulkTransferView(View):
    def get(self, request, payment_id):
        bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
        log_path = os.path.join(LOG_DIR, f"transferencia_bulk_{payment_id}.log")
        schema_path = os.path.join(SCHEMA_DIR, f"pain001_bulk_{payment_id}.xml")
        with open(log_path, 'w') as log:
            log.write(f"Simulando envío de transferencia masiva {payment_id}\n")
        with open(schema_path, 'w') as schema:
            schema.write(f"<BulkTransfer><PaymentID>{payment_id}</PaymentID></BulkTransfer>")
        messages.success(request, f"Transferencia masiva {payment_id} enviada.")
        return redirect('detalle_transferencia_bulk', payment_id=payment_id)

class EstadoBulkTransferView(View):
    def get(self, request, payment_id):
        bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
        bulk.transaction_status = "ACSP"
        bulk.save()
        log_path = os.path.join(LOG_DIR, f"transferencia_bulk_{payment_id}.log")
        with open(log_path, 'a') as log:
            log.write(f"Consulta de estado simulada para {payment_id} en {datetime.now()}\n")
        return redirect('detalle_transferencia_bulk', payment_id=payment_id)

class DetalleBulkTransferView(View):
    def get(self, request, payment_id):
        bulk = get_object_or_404(BulkTransfer, payment_id=payment_id)
        log_path = os.path.join(LOG_DIR, f"transferencia_bulk_{payment_id}.log")
        log_content = "Log no disponible"
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_content = f.read()
        return render(request, 'sepa_transferencias/detalle_bulk.html', {
            'transferencia': bulk,
            'log': log_content
        })

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def retry_second_factor(request, payment_id):
    session = get_oauth_session(request)
    headers = build_headers(request, 'PATCH')
    attach_common_headers(headers, 'PATCH')

    data = {
        "action": request.POST.get("action", "CREATE"),
        "authId": request.POST.get("authId")
    }

    url = f"https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{payment_id}"
    res = session.patch(url, json=data, headers=headers)

    log_path = os.path.join(LOG_DIR, f"transferencia_{payment_id}.log")
    with open(log_path, 'a') as log:
        log.write(f"\nPATCH OTP Retry:\nHeaders: {headers}\n\nBody: {data}\n\nResponse: {res.text}\n")

    if res.status_code == 200:
        messages.success(request, "OTP actualizado correctamente.")
        return redirect('detalle_transferencia', payment_id=payment_id)
    else:
        mensaje = handle_error_response(res)
        messages.error(request, f"Error al reintentar OTP: {mensaje}")
        return redirect('detalle_transferencia', payment_id=payment_id)

