import hashlib
from datetime import datetime
import os

LOG_DIR = os.path.join("logs", "transferencias")
SCHEMA_DIR = os.path.join("schemas", "transferencias")


def generate_payment_id(prefix=""):
    return f"{prefix}{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"[:35]

def generate_deterministic_id(*args, prefix=""):
    raw = ''.join(str(a) for a in args)
    hash_val = hashlib.sha256(raw.encode()).hexdigest()
    return (prefix + hash_val)[:35]

def obtener_ruta_schema_transferencia(payment_id):
    carpeta = os.path.join(SCHEMA_DIR, payment_id)
    os.makedirs(carpeta, exist_ok=True)
    return carpeta

def obtener_ruta_log_transferencia(payment_id):
    carpeta = os.path.join(LOG_DIR, payment_id)
    os.makedirs(carpeta, exist_ok=True)
    return os.path.join(carpeta, f"transferencia_{payment_id}.log")