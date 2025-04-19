import os
import requests
from django.shortcuts import render
from .models import SepaCreditTransfer, Debtor, Creditor
from .forms import SepaFilterForm

API_KEY = os.getenv('API_KEY')
API_URL = "https://api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"

def fetch_sepa_credit_transfers(request):
    """
    Vista para obtener datos de la API autenticada, almacenarlos en la base de datos y renderizarlos.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Obtener datos de la API
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return render(request, 'error.html', {'error_message': f"Error al conectar con la API: {str(e)}"})
    except ValueError:
        return render(request, 'error.html', {'error_message': "Error al procesar la respuesta de la API."})

    # Guardar datos en la base de datos
    SepaCreditTransfer.objects.all().delete()
    for item in data:
        debtor, _ = Debtor.objects.get_or_create(
            name=item['debtor']['debtorName'],
            country=item['debtor']['debtorPostalAddress']['country'],
            street_and_house_number=item['debtor']['debtorPostalAddress']['addressLine']['streetAndHouseNumber'],
            zip_code_and_city=item['debtor']['debtorPostalAddress']['addressLine']['zipCodeAndCity']
        )
        creditor, _ = Creditor.objects.get_or_create(
            name=item['creditor']['creditorName'],
            country=item['creditor']['creditorPostalAddress']['country'],
            street_and_house_number=item['creditor']['creditorPostalAddress']['addressLine']['streetAndHouseNumber'],
            zip_code_and_city=item['creditor']['creditorPostalAddress']['addressLine']['zipCodeAndCity']
        )
        SepaCreditTransfer.objects.create(
            payment_id=item['paymentId'],
            transaction_status=item['transactionStatus'],
            amount=item['instructedAmount']['amount'],
            currency=item['instructedAmount']['currency'],
            debtor=debtor,
            creditor=creditor
        )

    # Filtrar datos según el formulario
    form = SepaFilterForm(request.GET or None)
    transfers = SepaCreditTransfer.objects.all()
    if form.is_valid() and form.cleaned_data['transaction_status']:
        transfers = transfers.filter(transaction_status=form.cleaned_data['transaction_status'])

    return render(request, 'sepa_credit_transfers.html', {'form': form, 'transfers': transfers})
