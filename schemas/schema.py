# schema.py
import json
import os

def sepa_credit_transfer_schema():
    path = os.path.join(os.path.dirname(__file__), 'dbapi-SCT.json')
    with open(path, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    return spec.get('components', {}).get('schemas', {})


def one_time_passwords_schema():
    path = os.path.join(os.path.dirname(__file__), 'dbapi-OTP.json')
    with open(path, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    return spec.get('components', {}).get('schemas', {})


def transaction_authorization_schema():
    path = os.path.join(os.path.dirname(__file__), 'dbapi-TA.json')
    with open(path, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    return spec.get('components', {}).get('schemas', {})




# validate_payload.py
from jsonschema import validate, ValidationError

def validar_sepa_request(payload: dict):
    schemas = sepa_credit_transfer_schema()
    sepa_schema = schemas['SepaCreditTransferRequest']
    validate(instance=payload, schema=sepa_schema)

if __name__ == '__main__':
    ejemplo = {
        "messageId": "MSG-123",
        "creditor": {
            "name": "ACME Corp",
            "iban": "DE89370400440532013000"
        },
        "amount": 1500.75,
        "currency": "EUR"
    }
    try:
        validar_sepa_request(ejemplo)
        print("✅ Payload válido.")
    except ValidationError as e:
        print("❌ Error de validación:", e.message)