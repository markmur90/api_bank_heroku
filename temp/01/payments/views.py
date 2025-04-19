from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import PaymentRequest, PaymentResponse, CurrencyCode, IBAN, AccountReference, Amount, Address
from .forms import PaymentRequestForm, CurrencyCodeForm, IBANForm, AccountReferenceForm, AmountForm, AddressForm
import uuid
import requests
from config import settings
from core.oauth_app.views import get_authorization_code, exchange_code_for_token

def generate_end_to_end_identification():
    return f"DEUT{uuid.uuid4().hex[:30]}"

def get_otp():
    correlation_id = str(uuid.uuid4())
    headers = {
        'Correlation-Id': correlation_id
    }
    data = {
        "method": "PUSHTAN",
        "requestType": "INSTANT_SEPA_CREDIT_TRANSFERS",
        "requestData": {
            "targetIban": "DE86500700100925993805",
            "amountCurrency": "EUR",
            "amountValue": 512000.0
        }
    }
    response = requests.post('https://api.db.com:443/gw/dbapi/others/transactionAuthorization/v1/challenges', headers=headers, json=data)
    response_data = response.json()
    return response_data.get('otp', '')

def get_access_token():
    # Simula una solicitud para obtener el código de autorización
    request = requests.Request()
    response = get_authorization_code(request)
    code = response.url.split('code=')[1]

    # Intercambia el código de autorización por un token de acceso
    request.GET = {'code': code}
    token_response = exchange_code_for_token(request)
    return token_response.json().get('access_token')

def initiate_payment(request):
    if request.method == 'POST':
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            payment_request = form.save(commit=False)
            payment_request.end_to_end_identification = generate_end_to_end_identification()
            payment_request.save()
            payment_id = f"DEUT{uuid.uuid4().hex[:30]}"
            otp = get_otp()
            correlation_id = str(uuid.uuid4())
            token = get_access_token()  # Obtén el token de acceso automáticamente

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
            response = requests.post('https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers', headers=headers, json=data)
            response_data = response.json()
            return JsonResponse(response_data, status=response.status_code)
    else:
        form = PaymentRequestForm(initial={'end_to_end_identification': generate_end_to_end_identification()})
    return render(request, 'payments/initiate_payment.html', {'form': form})

def check_payment_status(request, payment_id):
    correlation_id = str(uuid.uuid4())
    headers = {
        'Correlation-Id': correlation_id
    }
    response = requests.get(f'https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers/{payment_id}', headers=headers)
    response_data = response.json()
    return JsonResponse(response_data)

def check_iban_reachability(request, iban):
    correlation_id = str(uuid.uuid4())
    headers = {
        'Correlation-Id': correlation_id
    }
    response = requests.get(f'https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers/creditorAccounts/{iban}/reachabilityStatus', headers=headers)
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
