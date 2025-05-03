# paths.py
import os

SCHEMA_DIR = os.path.join("schemas", "transferencias")
os.makedirs(SCHEMA_DIR, exist_ok=True)

def obtener_ruta_schema_transferencia(payment_id):
    carpeta = os.path.join(SCHEMA_DIR, str(payment_id))
    os.makedirs(carpeta, exist_ok=True)
    return carpeta
