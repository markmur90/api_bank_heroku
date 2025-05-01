# schema.py
import json
import os

def sepa_credit_transfer_schema():
    path = os.path.join(os.path.dirname(__file__), 'dbapi-sepaCreditTransfer2.json')
    with open(path, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    return spec.get('components', {}).get('schemas', {})

