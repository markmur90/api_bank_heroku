import os
import base64
import hashlib
import requests
import uuid
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from config import settings
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from api_db_swift2.config import PORT, URL
from core.payments.models import PaymentRequest, PaymentResponse, CurrencyCode, IBAN, AccountReference, Amount, Address
from core.payments.forms import PaymentRequest2Form, PaymentRequestForm, CurrencyCodeForm, IBANForm, AccountReferenceForm, AmountForm, AddressForm
from core.oauth_app.views import get_authorization_code, exchange_code_for_token
from django.views.decorators.http import require_POST
from generated_token import access_token
from api_db_swift2.config import *
from transferencia.services import generar_pdf_transferencia

@require_POST
def generate_token(request):
    otp = get_otp()
    return JsonResponse({access_token: otp})

def generate_end_to_end_identification():
    return str(uuid.uuid4())

def get_otp():
    correlation_id = str(uuid.uuid4())
    headers = {
        'Correlation-Id': correlation_id 
    } 
    data = {
        "method": method,
        "requestType": requestType,
        "requestData": {
            "targetIban": targetIban,
            "amountCurrency": amountCurrency,
            "amountValue": amountValue
        }
    }

    # Generar el code_verifier
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8').rstrip('=')
    print("Code Verifier:", code_verifier)

    # Generar el code_challenge
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
    print("Code Challenge:", code_challenge)

    # Simular respuesta exitosa
    response_data = {
        "otp": code_challenge,
        "correlationId": correlation_id
    }
    
    # Guardar la respuesta en un archivo JSON
    with open(f"/home/markmur88/Documentos/swif/deploy/develop/05_api_db_swift_final/{correlation_id}.json", 'w') as json_file:
        json.dump(response_data, json_file)
    
    return response_data.get('otp', '')

def get_access_token():
    # Simula una solicitud para obtener el código de autorización
    request = requests.Request()
    response = get_authorization_code(request)
    code = response.url.split('code=')[1]

    # Intercambia el código de autorización por un token de acceso
    request.GET = {'code': code}
    token_response = exchange_code_for_token(request)
    return token_response.json().get(access_token)


def initiate_payment(request):
    if request.method == 'POST':
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            payment_request = form.save(commit=False)
            end_to_end_id = generate_end_to_end_identification()
            payment_request.end_to_end_identification = end_to_end_id
            payment_request.save()
            
            payment_id = str(uuid.uuid4())
            otp = get_otp()
            correlation_id = str(uuid.uuid4())
            #token = get_access_token()  # Obtén el token de acceso automáticamente
            token = access_token  # Obtén el token de acceso automáticamente

            headers = {
                'Authorization': f'Bearer {token}',
                'idempotency-id': str(uuid.uuid4()),
                'otp': otp,
                'Correlation-Id': correlation_id
            }
            data = {
                "debtorAccount": {
                    "currencyCode": payment_request.debtor_account.currency_code.currency_code,
                    "iban": payment_request.debtor_account.iban.iban
                },
                "instructedAmount": {
                    "amount": float(payment_request.instructed_amount.amount),
                    "currencyCode": payment_request.instructed_amount.currency_code.currency_code
                },
                "creditorName": payment_request.creditor_name,
                "creditorAccount": {
                    "currencyCode": payment_request.creditor_account.currency_code.currency_code,
                    "iban": payment_request.creditor_account.iban.iban
                }
            }
            response = requests.post(f"https://api.dbapi.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers", json=data, headers=headers, verify=False)
            
            # Simular respuesta positiva
            response_data = {
                "transactionStatus": "ACCP",
                "paymentId": payment_id,
                "transactionId": str(uuid.uuid4())
            }
            
            # Generar PDF y guardar en el directorio media
            pdf_path = generar_pdf_transferencia(payment_request)

            # Guardar el PDF en el directorio media utilizando BASE_DIR
            media_path = os.path.join(settings.BASE_DIR, 'media', f"{end_to_end_id}.pdf")
            with open(media_path, 'wb') as media_file:
                with open(pdf_path, 'rb') as pdf_file:
                    media_file.write(pdf_file.read())

            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            return HttpResponse(pdf_data, content_type='application/pdf')
        else:
            return render(request, 'payments/initiate_payment.html', {'form': form, 'errors': form.errors})
    else:
        form = PaymentRequestForm(initial={'end_to_end_identification': generate_end_to_end_identification()})
    
    return render(request, 'payments/initiate_payment.html', {'form': form})

@login_required
@csrf_exempt
def initiate_payment2(request):
    if request.method == "POST":
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            payment_request = form.save(commit=False)
            end_to_end_id = generate_end_to_end_identification()
            payment_request.end_to_end_identification = end_to_end_id
            payment_request.save()
            payment_id = str(uuid.uuid4())
            otp = get_otp()
            correlation_id = str(uuid.uuid4())
            token = get_access_token()  # Obtén el token de acceso automáticamente
            
            # Enviar los datos al banco en formato JSON
            data = {
                "debtorAccount": {
                    "currencyCode": payment_request.debtor_account.currency_code.currency_code,
                    "iban": payment_request.debtor_account.iban.iban
                },
                "instructedAmount": {
                    "amount": float(payment_request.instructed_amount.amount),
                    "currencyCode": payment_request.instructed_amount.currency_code.currency_code
                },
                "creditorName": payment_request.creditor_name,
                "creditorAccount": {
                    "currencyCode": payment_request.creditor_account.currency_code.currency_code,
                    "iban": payment_request.creditor_account.iban.iban
                },
                "remittanceInformationUnstructured": payment_request.remittance_information_unstructured,
                "endToEndIdentification": payment_request.end_to_end_identification
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "idempotency-id": str(uuid.uuid4()),
                "otp": otp,
                "Correlation-Id": correlation_id
            }
            response = requests.post(f"https://api.dbapi.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers", json=data, headers=headers, verify=False)
            
            # Actualizar estado y ID de transacción si la transferencia fue exitosa
            if response.status_code == 200:
                payment_request.estado = response.json().get("estado", "completado")
                payment_request.payment_reference = response.json().get("payment_reference", payment_request.payment_reference)
                payment_request.transaction_id = response.json().get("transaction_id", payment_request.transaction_id)
            else:
                payment_request.estado = "fallido"
            payment_request.save()

            # Generar PDF y guardar en el directorio media
            pdf_path = generar_pdf_transferencia(payment_request)

            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            return HttpResponse(pdf_data, content_type='application/pdf')
        else:
            return render(request, "payments/initiate_payment2.html", {"form": form, "errors": form.errors})
    else:
        form = PaymentRequestForm()
    return render(request, "payments/initiate_payment2.html", {"form": form})

def initiate_payment3(request):
    if request.method == "POST":
        form = PaymentRequest2Form(request.POST)
        if form.is_valid():
            payment_request = form.save(commit=False)
            end_to_end_id = generate_end_to_end_identification()
            payment_request.end_to_end_identification = end_to_end_id
            payment_request.save()
            payment_id = str(uuid.uuid4())
            otp = get_otp()
            correlation_id = str(uuid.uuid4())
            token = access_token  # Obtén el token de acceso automáticamente

            headers = {
                'Authorization': f'Bearer {token}',
                'idempotency-id': str(uuid.uuid4()),
                'otp': otp,
                'Correlation-Id': correlation_id
            }
            data = {
                "debtorAccount": {
                    "currencyCode": payment_request.debtor_account.currency_code.currency_code,
                    "iban": payment_request.debtor_account.iban.iban
                },
                "instructedAmount": {
                    "amount": float(payment_request.instructed_amount.amount),
                    "currencyCode": payment_request.instructed_amount.currency_code.currency_code
                },
                "creditorName": payment_request.creditor_name,
                "creditorAccount": {
                    "currencyCode": payment_request.creditor_account.currency_code.currency_code,
                    "iban": payment_request.creditor_account.iban.iban
                },
                "creditorBank": payment_request.creditor_bank,
                "creditorAgent": payment_request.creditor_agent,
                "creditorAddress": {
                    "buildingNumber": payment_request.creditor_address.building_number,
                    "city": payment_request.creditor_address.city,
                    "country": payment_request.creditor_address.country,
                    "postalCode": payment_request.creditor_address.postal_code,
                    "street": payment_request.creditor_address.street
                },
                "debtorName": payment_request.debtor_name,
                "debtorBank": payment_request.debtor_bank,
                "debtorAgent": payment_request.debtor_agent,
                "debtorAddress": {
                    "buildingNumber": payment_request.debtor_address.building_number,
                    "city": payment_request.debtor_address.city,
                    "country": payment_request.debtor_address.country,
                    "postalCode": payment_request.debtor_address.postal_code,
                    "street": payment_request.debtor_address.street
                },
                "remittanceInformationUnstructured": payment_request.remittance_information_unstructured
            }
            response = requests.post(f"https://api.dbapi.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers", headers=headers, json=data)
                        
            if response.status_code == 200:
                payment_request.estado = response.json().get("estado", "completado")
                payment_request.payment_reference = response.json().get("payment_reference", payment_request.payment_reference)
                payment_request.swift_transaction_id = response.json().get("swift_transaction_id", payment_request.swift_transaction_id)
            else:
                payment_request.estado = "fallido"
            payment_request.save()
            
            # Generar PDF y guardar en el directorio media
            pdf_path = generar_pdf_transferencia(payment_request)

            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            return HttpResponse(pdf_data, content_type='application/pdf')
        else:
            return render(request, "payments/initiate_payment3.html", {"form": form, "errors": form.errors})
    else:
        form = PaymentRequest2Form()
    return render(request, "payments/initiate_payment3.html", {"form": form})

def check_payment_status(request, payment_id):
    correlation_id = str(uuid.uuid4())
    headers = {
        'Correlation-Id': correlation_id
    }
    response = requests.get(f"https://api.dbapi.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers/{payment_id}", headers=headers)
    response_data = response.json()
    return JsonResponse(response_data)

def check_iban_reachability(request, iban):
    correlation_id = str(uuid.uuid4())
    headers = {
        'Correlation-Id': correlation_id
    }
    response = requests.get(f"https://api.dbapi.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers/creditorAccounts/{iban}/reachabilityStatus", headers=headers)
    response_data = response.json()
    return JsonResponse(response_data)

def load_data(request):
    currency_codes = CurrencyCode.objects.all()
    ibans = IBAN.objects.all()
    account_references = AccountReference.objects.all()
    addresses = Address.objects.all()
    amounts = Amount.objects.all()
    return render(request, 'payments/load_data.html', {
        'currency_codes': currency_codes,
        'ibans': ibans,
        'account_references': account_references,
        'addresses': addresses,
        'amounts': amounts
    })

def load_currency_code(request):
    currency_codes = CurrencyCode.objects.all()
    if request.method == 'POST':
        form = CurrencyCodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('data_loaded_success')
    else:
        form = CurrencyCodeForm()
    return render(request, 'payments/load_currency_code.html', {'form': form, 'currency_codes': currency_codes})

def load_iban(request):
    ibans = IBAN.objects.all()
    if request.method == 'POST':
        form = IBANForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('data_loaded_success')
    else:
        form = IBANForm()
    return render(request, 'payments/load_iban.html', {'form': form, 'ibans': ibans})

def load_account_reference(request):
    currency_codes = CurrencyCode.objects.all()
    ibans = IBAN.objects.all()
    account_references = AccountReference.objects.all()
    if request.method == 'POST':
        form = AccountReferenceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('data_loaded_success')
    else:
        form = AccountReferenceForm()
    return render(request, 'payments/load_account_reference.html', {
        'form': form,
        'currency_codes': currency_codes,
        'ibans': ibans,
        'account_references': account_references
    })
 
def load_amount(request):
    currency_codes = CurrencyCode.objects.all()
    amounts = Amount.objects.all()
    if request.method == 'POST':
        form = AmountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('data_loaded_success')
    else:
        form = AmountForm()
    return render(request, 'payments/load_amount.html', {'form': form, 'currency_codes': currency_codes, 'amounts': amounts})

def load_address(request):
    addresses = Address.objects.all()
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('data_loaded_success')
    else:
        form = AddressForm()
    return render(request, 'payments/load_address.html', {'form': form, 'addresses': addresses})

def data_loaded_success(request):
    return render(request, 'payments/data_loaded_success.html')

def dashboard(request):
    return render(request, 'dashboard/dashboard.html')

