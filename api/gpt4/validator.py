# utils/validators.py

from datetime import datetime


def preparar_request_type_y_datos(schema_data):
    """
    Determina el tipo de request para la generación del OTP o autorización de transacción
    en función del campo `instantTransfer` y prepara los datos básicos requeridos por la API.
    """
    instant_transfer_value = schema_data.get("instantTransfer", False)

    # Validar que instantTransfer sea booleano
    if not isinstance(instant_transfer_value, bool):
        raise ValueError("El campo 'instantTransfer' debe ser un valor booleano.")

    is_instant = instant_transfer_value
    request_type = "INSTANT_SEPA_CREDIT_TRANSFERS" if is_instant else "SEPA_TRANSFER_GRANT"

    datos = {
        "type": "challengeRequestDataInstantSepaCreditTransfers" if is_instant else "challengeRequestDataSepaPaymentTransfer",
        "targetIban": schema_data["creditorAccount"]["iban"],
        "amountCurrency": schema_data["instructedAmount"]["currency"],
        "amountValue": schema_data["instructedAmount"]["amount"]
    }

    return request_type, datos
