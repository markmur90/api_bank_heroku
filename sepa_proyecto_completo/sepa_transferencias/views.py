# Mejora global: integrar mensajes de error y registro en log para todas las vistas API
import os
from datetime import datetime
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import SepaCreditTransfer
from .utils import (
    get_oauth_session, build_headers, attach_common_headers,
    validate_headers, handle_error_response
)

LOG_DIR = os.path.join("logs", "transferencias")
os.makedirs(LOG_DIR, exist_ok=True)

# Enviar transferencia (completo)
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

# Estado transferencia mejorado
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
