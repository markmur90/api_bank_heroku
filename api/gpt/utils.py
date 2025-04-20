import logging
import uuid
from requests_oauthlib import OAuth2Session
from django.conf import settings
logger = logging.getLogger(__name__)

# Token de acceso dummy (debería obtenerse con autenticación OAuth real)
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ0Njk1MTE5LCJpYXQiOjE3NDQ2OTMzMTksImp0aSI6ImUwODBhMTY0YjZlZDQxMjA4NzdmZTMxMDE0YmE4Y2Y5IiwidXNlcl9pZCI6MX0.432cmStSF3LXLG2j2zLCaLWmbaNDPuVm38TNSfQclMg"

ORIGIN = 'https://api.db.com'

CLIENT_ID = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'

CLIENT_SECRET = 'V3TeQPIuc7rst7lSGLnqUGmcoAWVkTWug1zLlxDupsyTlGJ8Ag0CRalfCbfRHeKYQlksobwRElpxmDzsniABTiDYl7QCh6XXEXzgDrjBD4zSvtHbP0Qa707g3eYbmKxO'


# Configuración OAuth2
OAUTH_CONFIG = {
    'client_id': str(CLIENT_ID),
    'client_secret': str(CLIENT_SECRET),
    'token_url': 'https://api.db.com/gw/oidc/token',
    'authorization_url': 'https://api.db.com/gw/oidc/authorize',
    'scopes': ['sepa_credit_transfers']
}

def get_oauth_session(request):
    """Crea sesión OAuth2 utilizando el access_token del entorno"""
    if not ACCESS_TOKEN:
        logger.error("ACCESS_TOKEN no está configurado en las variables de entorno")
        raise ValueError("ACCESS_TOKEN no está configurado")

    # Crear sesión OAuth2 con el token de acceso
    return OAuth2Session(client_id=OAUTH_CONFIG['client_id'], token={'access_token': ACCESS_TOKEN, 'token_type': 'Bearer'})


def generate_sepa_json_payload(transfer):
    """Genera el JSON de transferencia SEPA según especificación del banco"""
    return {
        "creditor": {
            "name": transfer.creditor.creditor_name,
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
            "name": transfer.debtor.debtor_name,
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
