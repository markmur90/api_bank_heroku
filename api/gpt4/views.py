import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import get_template
from weasyprint import HTML

from api.gpt4.models import Debtor, DebtorAccount, Creditor, CreditorAccount, CreditorAgent, PaymentIdentification, Transfer
from api.gpt4.forms import ClientIDForm, DebtorForm, DebtorAccountForm, CreditorForm, CreditorAccountForm, CreditorAgentForm, KidForm, ScaForm, SendTransferForm, TransferForm
from api.gpt4.utils import ZCOD_DIR, fetch_transfer_details, generar_pdf_transferencia, generate_deterministic_id, generate_payment_id_uuid, get_access_token, handle_error_response, obtener_otp_automatico_con_challenge, obtener_ruta_schema_transferencia, read_log_file, registrar_log, send_transfer, update_sca_request

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

# ==== CLIENT ID ====
def create_clientid(request):
    if request.method == 'POST':
        form = ClientIDForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_transferGPT4')
    else:
        form = ClientIDForm()
    return render(request, 'api/GPT4/create_clientid.html', {'form': form})

# ==== KID ====
def create_kid(request):
    if request.method == 'POST':
        form = KidForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_transferGPT4')
    else:
        form = KidForm()
    return render(request, 'api/GPT4/create_kid.html', {'form': form})

# ==== TRANSFER ====
def create_transfer(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.payment_id = str(generate_payment_id_uuid())
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

def transfer_detail1(request, transfer_id):
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

def send_transfer_view1(request, transfer_id):
    transfer = get_object_or_404(Transfer, id=transfer_id)
    # zcod_path = os.path.join(ZCOD_DIR, 'zCod.md')
    # zcod_content = ""
    # if os.path.exists(zcod_path):
    #     with open(zcod_path, 'r', encoding='utf-8') as f:
    #         zcod_content = f.read()
    # log_content = read_log_file(transfer.payment_id)
    # carpeta = obtener_ruta_schema_transferencia(transfer.payment_id)
    # archivos_logs = {archivo: os.path.join(carpeta, archivo) for archivo in os.listdir(carpeta) if archivo.endswith(".log")}
    # log_files_content = {}
    # mensaje_error = None
    # for nombre, ruta in archivos_logs.items():
    #     if os.path.exists(ruta):
    #         with open(ruta, 'r', encoding='utf-8') as f:
    #             contenido = f.read()
    #             log_files_content[nombre] = contenido
    #             if "=== Error ===" in contenido:
    #                 mensaje_error = contenido.split("=== Error ===")[-1].strip().split("===")[0].strip()
    if request.method == 'POST':
        form = SendTransferForm(request.POST)
        if not form.is_valid():
            registrar_log(transfer.payment_id, {}, "", error="Formulario inválido", extra_info="Errores de validación en vista")
            return redirect('transfer_detailGPT4', transfer_id=transfer.id)
        obtain_token = form.cleaned_data['obtain_token']
        manual_token = form.cleaned_data['manual_token']
        obtain_otp = form.cleaned_data['obtain_otp']
        manual_otp = form.cleaned_data['manual_otp']
        
        if obtain_token:
            try:
                token_to_use = get_access_token(transfer.payment_id, force_refresh=True)
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error obteniendo access_token en vista")
                return redirect('transfer_detailGPT4', transfer_id=transfer.id)
            regenerate_token = True
        else:
            token_to_use = manual_token
            regenerate_token = False
            
        if obtain_otp:
            try:
                otp_to_use, _ = obtener_otp_automatico_con_challenge(transfer)
                regenerate_otp = True
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error generando OTP automático en vista")
                return redirect('transfer_detailGPT4', transfer_id=transfer.id)
        else:
            otp_to_use = manual_otp
            regenerate_otp = False
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
            return redirect('transfer_detailGPT4', transfer_id=transfer.id)
    else:
        form = SendTransferForm()
        
    return render(request, 'api/GPT4/send_transfer.html', {
        'transfer': transfer,
        'form': form,
    })

def send_transfer_view2(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    form = SendTransferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        token = form.cleaned_data["manual_token"] or get_access_token(payment_id)
        otp = form.cleaned_data["manual_otp"] or obtener_otp_automatico_con_challenge(transfer)[0]
        send_transfer(transfer, token, otp)
        return redirect("transfer_detailGPT4", payment_id=payment_id)
    return render(request, "api/GPT4/send_transfer.html", {"form": form, "transfer": transfer})

# ==== ENVÍO DE TRANSFERENCIA ====
def send_transfer_view(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    form = SendTransferForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            obtain_token = form.cleaned_data['obtain_token']
            manual_token = form.cleaned_data['manual_token']
            obtain_otp = form.cleaned_data['obtain_otp']
            manual_otp = form.cleaned_data['manual_otp']
            # Obtener o usar token
            try:
                token = manual_token or (get_access_token(transfer.payment_id, force_refresh=True) if obtain_token else get_access_token(transfer.payment_id))
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error obteniendo access_token en vista")
                mensaje_error = str(e)
                return _render_transfer_detail(request, transfer, mensaje_error)
            # Obtener o usar OTP
            try:
                otp = manual_otp or (obtener_otp_automatico_con_challenge(transfer.payment_id)[0] if obtain_otp else obtener_otp_automatico_con_challenge(transfer.payment_id)[0])
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error generando OTP automático en vista")
                mensaje_error = str(e)
                return _render_transfer_detail(request, transfer, mensaje_error)
            # Intento de envío
            try:
                from api.gpt4.utils import send_transfer
                send_transfer(transfer.payment_id, token, otp)
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error enviando transferencia en vista")
                mensaje_error = str(e)
                return _render_transfer_detail(request, transfer, mensaje_error)
        else:
            registrar_log(transfer.payment_id, {}, "", error="Formulario inválido", extra_info="Errores de validación en vista")
            mensaje_error = "Debes seleccionar obtener TOKEN/OTP o proporcionar manualmente."
            return _render_transfer_detail(request, transfer, mensaje_error)
    return render(request, "api/GPT4/send_transfer.html", {"form": form, "transfer": transfer})


def transfer_update_sca1(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    form = ScaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        token  = get_access_token(transfer.payment_id)
        action = form.cleaned_data['action']
        otp    = form.cleaned_data['otp']
        update_sca_request(transfer, action, otp, token)
        return redirect('transfer_detailGPT4', payment_id=payment_id)
    return render(request, 'api/GPT4/transfer_sca.html', {'form': form, 'transfer': transfer})

# ==== AUTORIZACIÓN SCA ====
def transfer_update_sca(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    form = ScaForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            action = form.cleaned_data['action']
            otp = form.cleaned_data['otp']
            try:
                token = get_access_token(transfer.payment_id)
                from api.gpt4.utils import update_sca_request
                update_sca_request(transfer, action, otp, token)
                return redirect('transfer_detailGPT4', payment_id=payment_id)
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error procesando SCA en vista")
                mensaje_error = str(e)
                return _render_transfer_detail(request, transfer, mensaje_error)
        else:
            registrar_log(transfer.payment_id, {}, "", error="Formulario SCA inválido", extra_info="Errores validación SCA")
            mensaje_error = "Por favor corrige los errores en la autorización."
            return _render_transfer_detail(request, transfer, mensaje_error)
    return render(request, 'api/GPT4/transfer_sca.html', {'form': form, 'transfer': transfer})


def transfer_detail1(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    token = get_access_token(transfer.payment_id)
    details = fetch_transfer_details(transfer, token)
    
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
    
    return render(request, "api/GPT4/transfer_detail.html", {
        "transfer": transfer,
        "details": details,
        'log_files_content': log_files_content,
        'log_content': log_content,
        'archivos': archivos,
        'errores_detectados': errores_detectados,
        'mensaje_error': mensaje_error
    })

# ==== DETALLE DE TRANSFERENCIA ====
def transfer_detail(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    mensaje_error = None
    details = None
    try:
        token = get_access_token(transfer.payment_id)
        details = fetch_transfer_details(transfer, token)
    except Exception as e:
        registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error obteniendo detalles en vista")
        mensaje_error = str(e)
    return _render_transfer_detail(request, transfer, mensaje_error, details)

# ==== FUNCIÓN AUXILIAR PARA RENDERIZAR transfer_detail.html ====
def _render_transfer_detail(request, transfer, mensaje_error=None, details=None):
    log_content = read_log_file(transfer.payment_id)
    carpeta = obtener_ruta_schema_transferencia(transfer.payment_id)
    archivos = {
        nombre: os.path.join(carpeta, nombre)
        for nombre in [f"pain001_{transfer.payment_id}.xml", f"aml_{transfer.payment_id}.xml", f"pain002_{transfer.payment_id}.xml"]
        if os.path.exists(os.path.join(carpeta, nombre))
    }
    log_files_content = {}
    errores_detectados = []
    for fichero in os.listdir(carpeta):
        if fichero.endswith(".log"):
            ruta = os.path.join(carpeta, fichero)
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
                log_files_content[fichero] = contenido
                if "Error" in contenido or "Traceback" in contenido or "no válido según el XSD" in contenido:
                    errores_detectados.append(contenido)
    contexto = {
        'transfer': transfer,
        'details': details,
        'mensaje_error': mensaje_error,
        'log_files_content': log_files_content,
        'archivos': archivos,
        'errores_detectados': errores_detectados
    }
    return render(request, "api/GPT4/transfer_detail.html", contexto)

def edit_transfer1(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    if request.method == "POST":
        form = TransferForm(request.POST, instance=transfer)
        if form.is_valid():
            form.save()
            messages.success(request, "Transferencia actualizada correctamente.")
            return redirect('transfer_detailGPT4', payment_id=payment_id)
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = TransferForm(instance=transfer)
    return render(request, 'api/GPT4/edit_transfer.html', {
        'form': form,
        'transfer': transfer
    })

def edit_transfer(request, payment_id):
    transfer = get_object_or_404(Transfer, payment_id=payment_id)
    # Dos formularios: uno para editar la transferencia, otro para enviarla
    if request.method == "POST":
        form_edit = TransferForm(request.POST, instance=transfer)
        form_send = SendTransferForm(request.POST)

        # Si vienen datos del form de edición
        if "save_transfer" in request.POST and form_edit.is_valid():
            form_edit.save()
            messages.success(request, "Transferencia actualizada correctamente.")
            return redirect('transfer_detailGPT4', payment_id=payment_id)
        # Si vienen datos del form de envío
        elif "send_transfer" in request.POST and form_send.is_valid():
            obtain_token = form_send.cleaned_data['obtain_token']
            manual_token = form_send.cleaned_data['manual_token']
            obtain_otp = form_send.cleaned_data['obtain_otp']
            manual_otp = form_send.cleaned_data['manual_otp']

            # Obtener o usar token
            try:
                token = (
                    manual_token
                    or (get_access_token(transfer.payment_id, force_refresh=True) if obtain_token else get_access_token(transfer.payment_id))
                )
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error obteniendo access_token")
                messages.error(request, f"Error obteniendo token: {e}")
                return redirect('transfer_detailGPT4', payment_id=payment_id)

            # Obtener o usar OTP
            try:
                if obtain_otp:
                    otp, _ = obtener_otp_automatico_con_challenge(transfer.payment_id)
                else:
                    otp = manual_otp
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error generando OTP")
                messages.error(request, f"Error obteniendo OTP: {e}")
                return redirect('transfer_detailGPT4', payment_id=payment_id)

            # Intento de envío
            try:
                send_transfer(transfer.payment_id, token, otp)
                messages.success(request, "Transferencia enviada correctamente.")
            except Exception as e:
                registrar_log(transfer.payment_id, {}, "", error=str(e), extra_info="Error enviando transferencia")
                messages.error(request, f"No se pudo enviar la transferencia: {e}")

            return redirect('transfer_detailGPT4', payment_id=payment_id)

        else:
            # Validación fallida
            if "save_transfer" in request.POST:
                messages.error(request, "Por favor corrige los errores en el formulario de edición.")
            else:
                messages.error(request, "Por favor corrige los errores en el formulario de envío.")
    else:
        form_edit = TransferForm(instance=transfer)
        form_send = SendTransferForm()

    return render(request, 'api/GPT4/edit_transfer.html', {
        'form_edit': form_edit,
        'form_send': form_send,
        'transfer': transfer
    })

# ==== PDF ====
def descargar_pdf(request, payment_id):
    transferencia = get_object_or_404(Transfer, payment_id=payment_id)
    generar_pdf_transferencia(transferencia)
    carpeta = obtener_ruta_schema_transferencia(payment_id)
    pdf_file = next(
        (os.path.join(carpeta, f) for f in os.listdir(carpeta) if f.endswith(".pdf") and payment_id in f),
        None
    )
    if not pdf_file or not os.path.exists(pdf_file):
        messages.error(request, "El archivo PDF no se encuentra disponible.")
        return redirect('transfer_detailGPT4', payment_id=transferencia.payment_id)
    return FileResponse(open(pdf_file, 'rb'), content_type='application/pdf', as_attachment=True, filename=os.path.basename(pdf_file))
