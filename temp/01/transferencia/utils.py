from django.core.mail import send_mail
from api_db_swift2 import settings, config
from config import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SwiftTransaction
from .serializers import SwiftTransactionSerializer
import requests
from .utils import send_notification, obtener_token_acceso
from .exceptions import SwiftServerError, InvalidTransactionData

def send_notification(email, subject, message):
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

def obtener_token_acceso():
    url = f"{settings.DEUTSCHE_BANK_API['BASE_URL']}auth/token"
    auth = (settings.DEUTSCHE_BANK_API['CLIENT_ID'], settings.DEUTSCHE_BANK_API['CLIENT_SECRET'])
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials'}

    try:
        response = requests.post(url, headers=headers, data=data, auth=auth)
        response.raise_for_status()
    except requests.RequestException:
        raise Exception("Error al obtener el token de acceso")

    return response.json().get('access_token')



class SwiftTransactionViewL(APIView):
    def post(self, request):
        data = request.data
        interbank_required = settings.SWIFT_SETTINGS['INTERBANK_BLOCKING_CODE_REQUIRED']
        
        if interbank_required and not data.get('interbank_blocking_code'):
            raise InvalidTransactionData("Interbank Blocking Code is required")
        
        serializer = SwiftTransactionSerializer(data=data)
        if serializer.is_valid():
            transaction = serializer.save()
            
            # Simulación de envío a Swift
            swift_url = settings.SWIFT_SETTINGS['SERVER_URL']
            swift_port = settings.SWIFT_SETTINGS['SERVER_PORT']
            url = f"{swift_url}:{swift_port}/swift/transfer"
            
            try:
                response = requests.post(url, json=serializer.data, timeout=10)
                response.raise_for_status()
            except requests.RequestException:
                transaction.status = 'FAILED'
                transaction.save()
                send_notification("markmur88@proton.me", "Swift Transfer Failed", f"Transaction {transaction.id} failed.")
                raise SwiftServerError("Transfer failed")
            
            transaction.status = 'COMPLETED'
            transaction.save()
            send_notification("markmur88@proton.me", "Swift Transfer Completed", f"Transaction {transaction.id} was successful.")
            return Response({"message": "Transfer completed successfully"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class SwiftTransactionView(APIView):
    def post(self, request):
        data = request.data
        serializer = SwiftTransactionSerializer(data=data)

        if serializer.is_valid():
            transaction = serializer.save()

            # Datos para la solicitud al banco
            headers = {
                'Authorization': f'Bearer {settings.SWIFT_SETTINGS["BANK_API_KEY"]}',
                'Content-Type': 'application/json'
            }
            payload = {
                "transaction_id": transaction.transaction_id,
                "sender_bank": transaction.sender_bank,
                "receiver_reference": transaction.receiver_reference,
                "amount": str(transaction.amount),
                "currency": transaction.currency,
                "account_number": transaction.account_number
            }

            response = requests.post(settings.SWIFT_SETTINGS["BANK_API_URL"], json=payload, headers=headers)

            if response.status_code == 200:
                transaction.status = 'COMPLETED'
                transaction.save()
                return Response({"message": "Transferencia realizada con éxito"}, status=status.HTTP_200_OK)
            else:
                transaction.status = 'FAILED'
                transaction.save()
                return Response({"error": "Error en la transferencia"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IniciarTransferenciaSwiftView(APIView):
    def post(self, request):
        token = obtener_token_acceso()
        url = f"{settings.DEUTSCHE_BANK_API['BASE_URL']}payments/swift"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = {
            "monto": request.data.get("monto"),
            "moneda": request.data.get("moneda"),
            "cuenta_remitente": request.data.get("cuenta_remitente"),
            "cuenta_destinatario": request.data.get("cuenta_destinatario"),
            # Otros campos necesarios según la documentación de la API
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            return Response({"mensaje": "Transferencia iniciada con éxito"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Error al iniciar la transferencia"}, status=response.status_code)
