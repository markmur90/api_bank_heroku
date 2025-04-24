import hashlib
from datetime import datetime

def generate_payment_id(prefix=""):
    """
    Genera un ID único basado en la fecha y hora actual con un prefijo opcional.
    Máximo 35 caracteres.
    """
    return f"{prefix}{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"[:35]


def generate_deterministic_id(*args, prefix=""):
    """
    Genera un ID determinista con prefijo (opcional) a partir de valores concatenados.
    Máximo 35 caracteres, letras y números.
    """
    raw = ''.join(str(a) for a in args)
    hash_val = hashlib.sha256(raw.encode()).hexdigest()
    return (prefix + hash_val)[:35]
