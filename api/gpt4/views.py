import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from api.gpt4.models import Debtor, DebtorAccount, Creditor, CreditorAccount, CreditorAgent, PaymentIdentification, Transfer
from api.gpt4.forms import DebtorForm, DebtorAccountForm, CreditorForm, CreditorAccountForm, CreditorAgentForm, SendTransferForm, TransferForm
from api.gpt4.utils import ZCOD_DIR, generar_pdf_transferencia, generate_deterministic_id, generate_payment_id_uuid, get_access_token, handle_error_response, obtener_otp_automatico_con_challenge, obtener_ruta_schema_transferencia, read_log_file, registrar_log, send_transfer


logger = logging.getLogger(__name__)


# ==== DEBTOR ====
def create_debtor(request):
    if request.method == 'POST':
        form = DebtorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_debtorsGPT4')
    else:
        form = DebtorForm()
    return render(request, 'api/GPT4/create_debtor.html', {'form': form})

def list_debtors(request):
    debtors = Debtor.objects.all()
    return render(request, 'api/GPT4/list_debtor.html', {'debtors': debtors})

# ==== DEBTOR ACCOUNT ====
def create_debtor_account(request):
    if request.method == 'POST':
        form = DebtorAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_debtor_accountsGPT4')
    else:
        form = DebtorAccountForm()
    return render(request, 'api/GPT4/create_debtor_account.html', {'form': form})

def list_debtor_accounts(request):
    accounts = DebtorAccount.objects.all()
    return render(request, 'api/GPT4/list_debtor_accounts.html', {'accounts': accounts})

# ==== CREDITOR ====
def create_creditor(request):
    if request.method == 'POST':
        form = CreditorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_creditorsGPT4')
    else:
        form = CreditorForm()
    return render(request, 'api/GPT4/create_creditor.html', {'form': form})

def list_creditors(request):
    creditors = Creditor.objects.all()
    return render(request, 'api/GPT4/list_creditors.html', {'creditors': creditors})

# ==== CREDITOR ACCOUNT ====
def create_creditor_account(request):
    if request.method == 'POST':
        form = CreditorAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_creditor_accountsGPT4')
    else:
        form = CreditorAccountForm()
    return render(request, 'api/GPT4/create_creditor_account.html', {'form': form})

def list_creditor_accounts(request):
    accounts = CreditorAccount.objects.all()
    return render(request, 'api/GPT4/list_creditor_accounts.html', {'accounts': accounts})

# ==== CREDITOR AGENT ====
def create_creditor_agent(request):
    if request.method == 'POST':
        form = CreditorAgentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_creditor_agentsGPT4')
    else:
        form = CreditorAgentForm()
    return render(request, 'api/GPT4/create_creditor_agent.html', {'form': form})

def list_creditor_agents(request):
    agents = CreditorAgent.objects.all()
    return render(request, 'api/GPT4/list_creditor_agents.html', {'agents': agents})

# ==== TRANSFER ====
def create_transfer(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.payment_id = generate_payment_id_uuid()
            payment_identification = PaymentIdentification.objects.create(
                instruction_id=generate_deterministic_id(
                    transfer.payment_id,
                    transfer.creditor_account.iban,
                    transfer.instructed_amount
                ),
                end_to_end_id=generate_deterministic_id(
                    transfer.debtor_account.iban,
                    transfer.creditor_account.iban,
                    transfer.instructed_amount,
                    transfer.requested_execution_date,
                    prefix="E2E"
                )
            )
            transfer.payment_identification = payment_identification
            transfer.save()
            messages.success(request, "Transferencia creada correctamente.")
            return redirect('dashboard')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = TransferForm()
    return render(request, 'api/GPT4/create_transfer.html', {'form': form, 'transfer': None})



def list_transfers(request):
    estado = request.GET.get("estado")
    transfers = Transfer.objects.all().order_by('-created_at')

    if estado in ["PNDG", "RJCT", "ACSP"]:
        transfers = transfers.filter(status=estado)

    paginator = Paginator(transfers, 10)
    page_number = request.GET.get('page', 1)
    try:
        transfers_paginated = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        transfers_paginated = paginator.page(1)

    return render(request, 'api/GPT4/list_transfer.html', {
        'transfers': transfers_paginated
    })


def transfer_detail(request, transfer_id):
    transfer = get_object_or_404(Transfer, id=transfer_id)
    log_content = read_log_file(transfer.payment_id)
    carpeta = obtener_ruta_schema_transferencia(transfer.payment_id)
    archivos_logs = {
        archivo: os.path.join(carpeta, archivo)
        for archivo in os.listdir(carpeta)
        if archivo.endswith(".log")
    }
    log_files_content = {}
    mensaje_error = None
    for nombre, ruta in archivos_logs.items():
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
                log_files_content[nombre] = contenido
                if "=== Error ===" in contenido:
                    mensaje_error = contenido.split("=== Error ===")[-1].strip().split("===")[0].strip()
    archivos = {
        'pain001': os.path.join(carpeta, f"pain001_{transfer.payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"pain001_{transfer.payment_id}.xml")) else None,
        'aml': os.path.join(carpeta, f"aml_{transfer.payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"aml_{transfer.payment_id}.xml")) else None,
        'pain002': os.path.join(carpeta, f"pain002_{transfer.payment_id}.xml") if os.path.exists(os.path.join(carpeta, f"pain002_{transfer.payment_id}.xml")) else None,
    }
    errores_detectados = []
    for contenido in log_files_content.values():
        if "Error" in contenido or "Traceback" in contenido or "no válido según el XSD" in contenido:
            errores_detectados.append(contenido)
    return render(request, 'api/GPT4/transfer_detail.html', {
        'transfer': transfer,
        'log_files_content': log_files_content,
        'log_content': log_content,
        'archivos': archivos,
        'errores_detectados': errores_detectados,
        'mensaje_error': mensaje_error
    })



def send_transfer_view(request, transfer_id):
    transfer = get_object_or_404(Transfer, id=transfer_id)
    zcod_path = os.path.join(ZCOD_DIR, 'zCod.md')
    zcod_content = ""
    if os.path.exists(zcod_path):
        with open(zcod_path, 'r', encoding='utf-8') as f:
            zcod_content = f.read()
    log_content = read_log_file(transfer.payment_id)
    if request.method == 'POST':
        form = SendTransferForm(request.POST)
        if form.is_valid():
            obtain_token = form.cleaned_data['obtain_token']
            manual_token = form.cleaned_data['manual_token']
            obtain_otp   = form.cleaned_data['obtain_otp']
            manual_otp   = form.cleaned_data['manual_otp']
            if obtain_token:
                token_to_use     = get_access_token()
                regenerate_token = True
            else:
                token_to_use     = manual_token
                regenerate_token = False
            if obtain_otp:
                try:
                    otp_to_use, _ = obtener_otp_automatico_con_challenge(transfer)
                    regenerate_otp = True
                except Exception as e:
                    registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error generando OTP automático en vista")
                    form.add_error(None, f'Error generando OTP automático: {handle_error_response(e)}')
                    return render(request, 'api/GPT4/send_transfer.html', {
                        'transfer': transfer,
                        'form': form,
                        'zcod_content': zcod_content,
                        'log_content': log_content
                    })
            else:
                otp_to_use      = manual_otp
                regenerate_otp  = False
            try:
                send_transfer(
                    transfer,
                    use_token=token_to_use,
                    use_otp=otp_to_use,
                    regenerate_token=regenerate_token,
                    regenerate_otp=regenerate_otp
                )
                return redirect('transfer_detailGPT4', transfer_id=transfer.id)
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error enviando transferencia en vista")
                form.add_error(None, f'Error enviando transferencia: {handle_error_response(e)}')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = SendTransferForm()
    return render(request, 'api/GPT4/send_transfer.html', {
        'transfer': transfer,
        'form': form,
        'zcod_content': zcod_content,
        'log_content': log_content
    })



def descargar_pdf(request, payment_id):
    transferencia = get_object_or_404(Transfer, payment_id=payment_id)
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




