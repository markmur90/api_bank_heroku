from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest, HttpResponseServerError
from .models import SepaCreditTransfer, ErrorResponse
from .forms import SepaCreditTransferForm
from .utils import get_oauth_session, access_token, generate_sepa_json_payload
import uuid
import logging
from .helpers import generate_payment_id, generate_deterministic_id

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def initiate_sepa_transfer(request):
    if request.method == 'POST':
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'Accept': 'application/json'
        }
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            try:
                transfer = form.save(commit=False)
                transfer.payment_id = uuid.uuid4()
                transfer.auth_id = uuid.uuid4()
                transfer.transaction_status = 'PDNG'
                transfer.payment_identification.end_to_end_id = generate_payment_id("E2E")
                transfer.payment_identification.instruction_id = generate_deterministic_id(
                    transfer.creditor_account.iban,
                    transfer.instructed_amount.amount,
                    transfer.requested_execution_date
                )

                transfer.payment_identification.save()
                transfer.save()

                payload = generate_sepa_json_payload(transfer)

                headers.update({
                    'Content-Type': 'application/json',
                    'otp': request.POST.get('otp', 'PUSHTAN'),
                    'Correlation-ID': str(uuid.uuid4()),
                    'Authorization': f"Bearer {access_token}",
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': request.get_host(),
                })

                oauth = get_oauth_session(request)
                response = oauth.post(
                    'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer',
                    json=payload,
                    headers=headers
                )

                if response.status_code == 201:
                    return render(request, 'api/SCT/transfer_success.html', {
                        'payment_id': transfer.payment_id,
                        'execution_date': transfer.requested_execution_date,
                        'creditor': transfer.creditor.creditor_name,
                        'debtor': transfer.debtor.debtor_name
                    })
                else:
                    ErrorResponse.objects.create(
                        code=response.status_code,
                        message=response.text,
                        message_id=headers['idempotency-id']
                    )
                    return HttpResponseBadRequest("Error en la operación bancaria")

            except Exception as e:
                ErrorResponse.objects.create(
                    code=500,
                    message=str(e),
                    message_id=headers.get('idempotency-id', '')
                )
                return HttpResponseServerError("Error interno del servidor")
    else:
        form = SepaCreditTransferForm()

    return render(request, 'api/SCT/initiate_transfer.html', {'form': form})


def check_transfer_status(request, payment_id):
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'Accept': 'application/json',
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {access_token}",
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': request.get_host(),
        }

        response = oauth.get(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer/{payment_id}/status',
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            new_status = data.get('transactionStatus')
            if new_status:
                transfer.transaction_status = new_status
                transfer.save()
        else:
            logger.warning(f"Respuesta no exitosa del banco: {response.status_code} - {response.text}")

        return render(request, 'api/SCT/transfer_status.html', {
            'transfer': transfer,
            'bank_response': response.json() if response.ok else None
        })

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error consultando estado: {str(e)}"
        )
        return render(request, 'api/SCT/transfer_status.html', {
            'transfer': transfer,
            'error': str(e)
        })


@require_http_methods(["POST"])
def cancel_sepa_transfer(request, payment_id):
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'otp': request.POST.get('otp', 'PUSHTAN'),
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {access_token}",
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': request.get_host(),
        }

        response = oauth.delete(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer/{payment_id}',
            headers=headers
        )

        if response.status_code == 200:
            transfer.transaction_status = 'CANC'
            transfer.save()
            return render(request, 'api/SCT/cancel_success.html', {
                'transfer': transfer
            })
        else:
            ErrorResponse.objects.create(
                code=response.status_code,
                message=response.text,
                message_id=headers['idempotency-id']
            )
            return HttpResponseBadRequest("No se pudo cancelar la transferencia.")

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error en cancelación: {str(e)}"
        )
        return HttpResponseServerError("Error cancelando la transferencia")


@require_http_methods(["POST"])
def retry_sepa_transfer_auth(request, payment_id):
    try:
        transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)

        oauth = get_oauth_session(request)
        headers = {
            'idempotency-id': str(uuid.uuid4()),
            'otp': request.POST.get('otp', 'PUSHTAN'),
            'Correlation-ID': str(uuid.uuid4()),
            'Authorization': f"Bearer {access_token}",
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': request.get_host(),
        }

        payload = {
            "requestType": "SEPA_TRANSFER_GRANT"
        }

        response = oauth.patch(
            f'https://api.db.com:443/gw/dbapi/banking/transactions/v2/sepaCreditTransfer/{payment_id}',
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            return render(request, 'api/SCT/retry_success.html', {
                'transfer': transfer
            })
        else:
            ErrorResponse.objects.create(
                code=response.status_code,
                message=response.text,
                message_id=headers['idempotency-id']
            )
            return HttpResponseBadRequest("Error al reintentar la autenticación")

    except Exception as e:
        ErrorResponse.objects.create(
            code=500,
            message=f"Error en retry auth: {str(e)}"
        )
        return HttpResponseServerError("Error en retry autenticación")
