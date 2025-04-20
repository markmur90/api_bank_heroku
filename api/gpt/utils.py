import uuid
from requests_oauthlib import OAuth2Session
from django.conf import settings

# Token de acceso dummy (debería obtenerse con autenticación OAuth real)
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

def get_oauth_session(request):
    """Retorna una sesión OAuth2 configurada para hacer llamadas autenticadas"""
    return OAuth2Session(token={"access_token": access_token, "token_type": "Bearer"})


def generate_sepa_json_payload(transfer):
    """Genera el JSON de transferencia SEPA según especificación del banco"""
    return {
        "creditor": {
            "name": transfer.creditor.name,
            "account": {
                "iban": transfer.creditor_account.iban,
                "currency": transfer.creditor_account.currency
            },
            "agent": {
                "bic": transfer.creditor_agent.financial_institution_id if transfer.creditor_agent else None
            },
            "address": {
                "country": transfer.creditor.postal_address.country,
                "zipCodeAndCity": transfer.creditor.postal_address.zip_code_and_city,
                "streetAndHouseNumber": transfer.creditor.postal_address.street_and_house_number
            }
        },
        "debtor": {
            "name": transfer.debtor.name,
            "account": {
                "iban": transfer.debtor_account.iban,
                "currency": transfer.debtor_account.currency
            },
            "address": {
                "country": transfer.debtor.postal_address.country,
                "zipCodeAndCity": transfer.debtor.postal_address.zip_code_and_city,
                "streetAndHouseNumber": transfer.debtor.postal_address.street_and_house_number
            }
        },
        "amount": {
            "currency": transfer.instructed_amount.currency,
            "amount": str(transfer.instructed_amount.amount)
        },
        "remittanceInformationUnstructured": transfer.remittance_information_unstructured,
        "requestedExecutionDate": transfer.requested_execution_date.strftime('%Y-%m-%d'),
        "endToEndId": transfer.payment_identification.end_to_end_id,
        "instructionId": transfer.payment_identification.instruction_id,
        "purposeCode": transfer.purpose_code,
        "priority": "High"  # Agregar prioridad (Instant SEPA Credit Transfer)
    }
