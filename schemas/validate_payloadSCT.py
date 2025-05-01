# validate_payload.py
from api.core.schemaSCT import sepa_credit_transfer_schema
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