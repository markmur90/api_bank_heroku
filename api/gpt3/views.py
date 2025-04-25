import os
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

from api.gpt3.generate_aml import generar_archivo_aml
from api.gpt3.generate_xml import generar_xml_pain001

from api.gpt3.models import *
from api.gpt3.forms import *
from api.gpt3.utils import (
    build_complete_sepa_headers, generar_pdf_transferencia, get_oauth_session, build_headers, attach_common_headers,
    validate_headers, handle_error_response
)
from api.gpt3.helpers import generate_deterministic_id, generate_payment_id, generate_payment_id_uuid, obtener_ruta_log_transferencia, obtener_ruta_schema_transferencia


@login_required
def descargar_pdf(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    generar_pdf_transferencia(transferencia)  # Siempre asegura que se genera el PDF más reciente
    carpeta_transferencia = obtener_ruta_schema_transferencia(payment_id)

    pdf_archivo = next(
        (os.path.join(carpeta_transferencia, f) for f in os.listdir(carpeta_transferencia)
         if f.endswith(".pdf") and payment_id in f),
        None
    )

    if not pdf_archivo or not os.path.exists(pdf_archivo):
        messages.error(request, "El archivo PDF no se encuentra disponible.")
        return redirect('detalle_transferencia', payment_id=payment_id)

    return FileResponse(open(pdf_archivo, 'rb'), content_type='application/pdf', as_attachment=True, filename=os.path.basename(pdf_archivo))


@login_required
def crear_transferencia(request):
    if request.method == 'POST':
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            transferencia = form.save(commit=False)
            transferencia.payment_id = generate_payment_id_uuid()

            # Generar instruction_id determinista sin prefijo
            transferencia.payment_identification.instruction_id = generate_deterministic_id(
                transferencia.payment_id,
                transferencia.creditor_account.iban,
                transferencia.instructed_amount.amount
            )

            # Generar end_to_end_id con prefijo E2E
            transferencia.payment_identification.end_to_end_id = generate_deterministic_id(
                transferencia.debtor_account.iban,
                transferencia.creditor_account.iban,
                transferencia.instructed_amount.amount,
                transferencia.requested_execution_date,
                prefix="E2E"
            )

            transferencia.save()

            # Guardar archivos directamente al crear (pain.001 + AML)
            generar_xml_pain001(transferencia, transferencia.payment_id)
            generar_archivo_aml(transferencia, transferencia.payment_id)

            messages.success(request, "Transferencia creada correctamente.")
            return redirect('listar_transferencias')
    else:
        form = SepaCreditTransferForm()
    return render(request, 'api/GPT3/crear_transferencia.html', {'form': form})


@login_required
def listar_transferencias(request):
    transferencias = SepaCreditTransfer.objects.all().order_by('-created_at')
    return render(request, 'api/GPT3/listar_transferencias.html', {'transferencias': transferencias})


@login_required
def detalle_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    log_path = obtener_ruta_log_transferencia(payment_id)
    log_content = "Log no disponible"
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log_content = f.read()

    carpeta = obtener_ruta_schema_transferencia(payment_id)
    xml_pain001 = os.path.join(carpeta, f"pain001_{payment_id}.xml")
    xml_pain002 = os.path.join(carpeta, f"pain002_{payment_id}.xml")
    aml_file = os.path.join(carpeta, f"aml_{payment_id}.txt")

    archivos = {
        'pain001': xml_pain001 if os.path.exists(xml_pain001) else None,
        'pain002': xml_pain002 if os.path.exists(xml_pain002) else None,
        'aml': aml_file if os.path.exists(aml_file) else None
    }

    return render(request, 'api/GPT3/detalle_transferencia.html', {
        'transferencia': transferencia,
        'log': log_content,
        'archivos': archivos
    })


@login_required
def enviar_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    headers = build_complete_sepa_headers(request, 'POST')
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
                "serviceLevelCode": "INST"
            },
            "localInstrument": {
                "localInstrumentCode": "INST"
            },
            "categoryPurpose": {
                "categoryPurposeCode": "SALA"
            }
        }
    }

    try:
        # Regenerar archivos XML y AML antes de envío
        generar_xml_pain001(transferencia, payment_id)
        generar_archivo_aml(transferencia, payment_id)

        res = session.post(
            'https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/',
            json=payload, headers=headers
        )

        log_path = obtener_ruta_log_transferencia(payment_id)
        with open(log_path, 'w') as log_file:
            log_file.write(f"Headers enviados:\n{headers}\n\n")
            log_file.write(f"Headers respuesta:\n{dict(res.headers)}\n\n")
            log_file.write(f"Body:\n{res.text}\n")

        if res.status_code not in [200, 201]:
            mensaje = handle_error_response(res)
            messages.error(request, f"Error al enviar transferencia: {mensaje}")
            return redirect('detalle_transferencia', payment_id=payment_id)

        # Guardar respuesta XML pain.002 si es proporcionada
        content_type = res.headers.get("Content-Type", "")
        if "xml" in content_type:
            carpeta_xml = obtener_ruta_schema_transferencia(payment_id)
            xml_response_path = os.path.join(carpeta_xml, f"pain002_{payment_id}.xml")
            with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
                xmlfile.write(res.text)

        transferencia.transaction_status = "PDNG"
        transferencia.save()
        messages.success(request, "Transferencia enviada, registrada y respuesta XML guardada.")
        return redirect('detalle_transferencia', payment_id=payment_id)

    except Exception as e:
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect('detalle_transferencia', payment_id=payment_id)  


@login_required
def estado_transferencia(request, payment_id):
    transferencia = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    session = get_oauth_session(request)
    headers = build_complete_sepa_headers(request, 'GET')

    url = f"https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer/{payment_id}/status"

    try:
        res = session.get(url, headers=headers)

        # Registrar en log
        log_path = obtener_ruta_log_transferencia(payment_id)
        with open(log_path, 'a') as log_file:
            log_file.write(f"\nConsulta de estado - {datetime.now()}\nHeaders enviados:\n{headers}\n\n")
            log_file.write(f"Headers respuesta:\n{dict(res.headers)}\n\n")
            log_file.write(f"Respuesta:\n{res.text}\n")

        if res.status_code == 200:
            # Guardar XML de respuesta si aplica
            content_type = res.headers.get("Content-Type", "")
            if "xml" in content_type:
                carpeta_xml = obtener_ruta_schema_transferencia(payment_id)
                xml_response_path = os.path.join(carpeta_xml, f"pain002_{payment_id}_estado.xml")
                with open(xml_response_path, "w", encoding="utf-8") as xmlfile:
                    xmlfile.write(res.text)

            transferencia.transaction_status = res.json().get("transactionStatus", transferencia.transaction_status)
            transferencia.save()
            messages.success(request, "Estado actualizado desde el banco.")
        else:
            mensaje = handle_error_response(res)
            messages.error(request, f"Error al consultar estado: {mensaje}")
        return render(request, 'api/GPT3/detalle_transferencia.html', {
            'transferencia': transferencia,
            'log': "Log no disponible",
            'archivos': {
                'pain001': os.path.join(obtener_ruta_schema_transferencia(payment_id), f"pain001_{payment_id}.xml"),
                'pain002': os.path.join(obtener_ruta_schema_transferencia(payment_id), f"pain002_{payment_id}.xml"),
                'aml': os.path.join(obtener_ruta_schema_transferencia(payment_id), f"aml_{payment_id}.txt"),
            'bank_response': res.json() if res.ok else None
            }
        })

    except Exception as e:
        messages.error(request, f"Error al consultar estado: {str(e)}")

    return redirect('detalle_transferencia', payment_id=payment_id)


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
            return redirect('listar_transferencias')

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

        return redirect('detalle_transferencia_bulk', payment_id=payment_id)


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

        return redirect('detalle_transferencia_bulk', payment_id=payment_id)


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
    try:
        res = session.patch(url, json=data, headers=headers)

        log_path = obtener_ruta_log_transferencia(payment_id)
        with open(log_path, 'a') as log:
            log.write(f"\nPATCH OTP Retry - {datetime.now()}\nHeaders: {headers}\n\nBody: {data}\n\nResponse: {res.text}\n")

        if res.status_code == 200:
            # Guardar XML de respuesta OTP si viene en formato XML
            content_type = res.headers.get("Content-Type", "")
            if "xml" in content_type:
                carpeta = obtener_ruta_schema_transferencia(payment_id)
                otp_xml_path = os.path.join(carpeta, f"otp_patch_{payment_id}.xml")
                with open(otp_xml_path, 'w', encoding='utf-8') as xmlfile:
                    xmlfile.write(res.text)

            messages.success(request, "OTP actualizado correctamente.")
        else:
            mensaje = handle_error_response(res)
            messages.error(request, f"Error al reintentar OTP: {mensaje}")

    except Exception as e:
        messages.error(request, f"Error inesperado al aplicar segundo factor: {str(e)}")

    return redirect('detalle_transferencia', payment_id=payment_id)


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

def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('account_listGPT')
    else:
        form = AccountForm()
    return render(request, 'api/GPT/create_account.html', {'form': form})


def create_amount(request):
    if request.method == 'POST':
        form = AmountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('amount_listGPT')
    else:
        form = AmountForm()
    return render(request, 'api/GPT/create_amount.html', {'form': form})


def create_financial_institution(request):
    if request.method == 'POST':
        form = FinancialInstitutionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('financial_institution_listGPT')
    else:
        form = FinancialInstitutionForm()
    return render(request, 'api/GPT/create_financial_institution.html', {'form': form})


def create_postal_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('postal_address_listGPT')
    else:
        form = AddressForm()
    return render(request, 'api/GPT/create_postal_address.html', {'form': form})


def create_payment_identification(request):
    if request.method == 'POST':
        form = PaymentIdentificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('initiate_transferGPT')
    else:
        form = PaymentIdentificationForm()
    return render(request, 'api/GPT/create_payment_identification.html', {'form': form})


def create_debtor(request):
    if request.method == 'POST':
        form = DebtorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('debtor_listGPT')
    else:
        form = DebtorForm()
    return render(request, 'api/GPT/create_debtor.html', {'form': form})


def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('creditor_listGPT')
    else:
        form = CreditorForm()
    return render(request, 'api/GPT/create_creditor.html', {'form': form})


