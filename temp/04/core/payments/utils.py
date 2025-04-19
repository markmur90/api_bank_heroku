from django.core.mail import send_mail
from api_db_swift2 import config
import requests

def send_notification(email, subject, message):
    send_mail(subject, message, config.DEFAULT_FROM_EMAIL, [email])

def obtener_token_acceso():
    url = f"{config.DEUTSCHE_BANK_API['BASE_URL']}auth/token"
    auth = (config.DEUTSCHE_BANK_API['CLIENT_ID'], config.DEUTSCHE_BANK_API['CLIENT_SECRET'])
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials'}

    try:
        response = requests.post(url, headers=headers, data=data, auth=auth)
        response.raise_for_status()
    except requests.RequestException:
        raise Exception("Error al obtener el token de acceso")

    return response.json().get('access_token')