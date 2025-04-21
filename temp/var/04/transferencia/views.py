from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, redirect
from transferencia.models import Transferencia
import requests
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
import os
from reportlab.lib.pagesizes import letter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, generics
from django.views.decorators.csrf import csrf_exempt
from api_db_swift2.config import SWIFT_TRANSFER_URL, CLIENT_ID, CLIENT_SECRET, SWIFT_URL_TOKEN, SWIFT_URL_REFRESH_TOKEN, SWIFT_URL_REVOKE_TOKEN, BANCO_ORIGEN
from api_db_swift2 import settings
from transferencia.services import generar_pdf_transferencia

class TransferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transferencia
        fields = '__all__'

    def create(self, validated_data):
        transferencia = Transferencia.objects.create(**validated_data)
        # Generar código de transacción
        transferencia.swift_transaction_id = f"TX-{transferencia.id}"
        transferencia.save()
        return transferencia

class TransferenciaViewSet(viewsets.ModelViewSet):
    queryset = Transferencia.objects.all()
    serializer_class = TransferenciaSerializer
    permission_classes = [IsAuthenticated]

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")  # Redirigir a la nueva plantilla
        else:
            return render(request, "dashboard/login.html", {"error": "Credenciales inválidas"})
    return render(request, "dashboard/login.html")

@login_required
@csrf_protect
def dashboard_view(request):
    transferencias = Transferencia.objects.filter(usuario=request.user)
    return render(request, "dashboard/dashboard.html", {"transferencias": transferencias})

@login_required
@csrf_exempt
def transferencia_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        token = request.POST.get('token')
        origin_iban = request.POST.get("origin_iban")
        origin_bic = request.POST.get("origin_bic")
        origin_account_number = request.POST.get("origin_account_number")  # Nuevo campo
        origin_account_holder_name = request.POST.get("origin_account_holder_name")  # Nuevo campo
        amount = request.POST.get("amount")
        currency_code = request.POST.get("currency_code")
        counter_party_bank_name = request.POST.get("counter_party_bank_name")
        counter_party_account_number = request.POST.get("counter_party_account_number")
        counter_party_name = request.POST.get("counter_party_name")
        counter_party_bic = request.POST.get("counter_party_bic")
        payment_reference = request.POST.get("payment_reference")
 
        # Guardar en la base de datos (ajustar según el modelo de Transferencia)
        serializer = TransferenciaSerializer(data=request.POST)
        if serializer.is_valid():
            transferencia = serializer.save(usuario=request.user)
            # Enviar los datos al banco en formato JSON
            data = [{
                "origin_iban": transferencia.origin_iban,
                "origin_bic": transferencia.origin_bic,
                "amount": float(transferencia.monto),
                "currency_code": transferencia.currency_code,
                "counter_party_bank_name": transferencia.counter_party_bank_name,
                "counter_party_account_number": transferencia.counter_party_account_number,
                "counter_party_name": transferencia.counter_party_name,
                "counter_party_bic": transferencia.counter_party_bic,
                "payment_reference": transferencia.payment_reference,
                "fecha": transferencia.fecha.strftime('%d/%m/%Y %H:%M:%S'),  # Agregar la fecha de la transacción
            }]
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            } 
            response = requests.post(SWIFT_TRANSFER_URL, json=data, headers=headers, verify=False)
            
            # Actualizar estado y ID de transacción SWIFT si la transferencia fue exitosa
            if response.status_code == 200:
                transferencia.estado = response.json().get("estado", "completado")
                transferencia.payment_reference = response.json().get("payment_reference", transferencia.payment_reference)
                transferencia.swift_transaction_id = response.json().get("swift_transaction_id", transferencia.swift_transaction_id)
            else:
                transferencia.estado = "fallido"
            transferencia.save()

            # Generar PDF y guardar en el directorio media
            pdf_path = generar_pdf_transferencia(transferencia)

            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            return HttpResponse(pdf_data, content_type='application/pdf')
        else:
            return render(request, "transferencia/transferencia.html", {"errors": serializer.errors})

    return render(request, "transferencia/transferencia.html")

@login_required
@csrf_protect
def transferencia_exitosa_view(request):
    return render(request, "transferencia/transferencia_exitosa.html")  # updated path  # updated path

@login_required
@csrf_protect
def dashboard_transferencias_view(request):
    transferencias = Transferencia.objects.filter(usuario=request.user)
    return render(request, "transferencia/lista_transferencias.html", {"transferencias": transferencias})  # updated path

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transferencia_list_view(request):
    transferencias = Transferencia.objects.filter(usuario=request.user)
    serializer = TransferenciaSerializer(transferencias, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transferencia_create_view(request):
    if request.method == 'POST':
        serializer = TransferenciaSerializer(data=request.data)
        if serializer.is_valid():
            transferencia = serializer.save(usuario=request.user)
            # Enviar los datos al banco en formato JSON
            data = [{
                "origin_iban": transferencia.origin_iban,
                "origin_bic": transferencia.origin_bic,
                "amount": float(transferencia.monto),
                "currency_code": transferencia.currency_code,
                "counter_party_bank_name": transferencia.counter_party_bank_name,
                "counter_party_account_number": transferencia.counter_party_account_number,
                "counter_party_name": transferencia.counter_party_name,
                "counter_party_bic": transferencia.counter_party_bic,
                "payment_reference": transferencia.payment_reference,
                "fecha": transferencia.fecha.strftime('%d/%m/%Y %H:%M:%S'),  # Agregar la fecha de la transacción
            }]
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {request.POST.get('token')}"
            }
            response = requests.post(SWIFT_TRANSFER_URL, json=data, headers=headers, verify=False)
            
            # Actualizar estado y ID de transacción SWIFT si la transferencia fue exitosa
            if response.status_code == 200:
                transferencia.estado = response.json().get("estado", "completado")
                transferencia.payment_reference = response.json().get("payment_reference", transferencia.payment_reference)
                transferencia.swift_transaction_id = response.json().get("swift_transaction_id", transferencia.swift_transaction_id)
                transferencia.save()
                return Response({"detail": "Transferencia completada"}, status=status.HTTP_201_CREATED)
            return Response({"detail": "Error en la transferencia"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": "Método no permitido"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@permission_classes([AllowAny])
def token(request):
    '''
    Gets tokens with username and password. Input should be in the format:
    {"username": "username", "password": "1234abcd"}
    '''
    r = requests.post(SWIFT_URL_TOKEN, 
        data={
            'grant_type': 'password',
            'username': request.data['username'],
            'password': request.data['password'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        },
    )
    return Response(r.json())

@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    '''
    Registers user to the server. Input should be in the format:
    {"refresh_token": "<token>"}
    '''
    r = requests.post(SWIFT_URL_REFRESH_TOKEN, 
        data={
            'grant_type': 'refresh_token',
            'refresh_token': request.data['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        },
    )
    return Response(r.json())

@api_view(['POST'])
@permission_classes([AllowAny])
def revoke_token(request):
    '''
    Method to revoke tokens.
    {"token": "<token>"}
    '''
    r = requests.post(SWIFT_URL_REVOKE_TOKEN, 
        data={
            'token': request.data['token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        },
    )
    # If it goes well return success message (would be empty otherwise) 
    if r.status_code == requests.codes.ok:
        return Response({'message': 'token revoked'}, r.status_code)
    # Return the error if it goes badly
    return Response(r.json(), r.status_code)


def initiate_payment2(request):
    if request.method == "POST":
        form = PaymentRequestForm(request.POST)
        if form.is_valid():
            payment_request = form.save(commit=False)
            end_to_end_id = generate_end_to_end_identification()
            payment_request.end_to_end_identification = end_to_end_id
            payment_request.save()
            
            # otp = get_otp()
            correlation_id = str(uuid.uuid4())
            token = access_token  # Obtén el token de acceso automáticamente

            headers = {
                'Authorization': f'Bearer {token}',
                'idempotency-id': str(uuid.uuid4()),
                'otp': otp,
                'Correlation-Id': correlation_id
            }
            data = {
                "debtorAccount": {
                    "currencyCode": payment_request.debtor_account.currency_code.currency_code,
                    "iban": payment_request.debtor_account.iban.iban
                },
                "instructedAmount": {
                    "amount": float(payment_request.instructed_amount.amount),
                    "currencyCode": payment_request.instructed_amount.currency_code.currency_code
                },
                "creditorName": payment_request.creditor_name,
                "creditorAccount": {
                    "currencyCode": payment_request.creditor_account.currency_code.currency_code,
                    "iban": payment_request.creditor_account.iban.iban
                }
            }
            # response = requests.post(f"https://{URL}:{PORT}/gw/dbapi/paymentInitiation/payments/v1/instantSepaCreditTransfers", headers=headers, json=data)            
            response = "ACCP"
            
            if response.status_code == "ACCP":
                payment_request.estado = "Preceding check of technical validation was successful. Customer profile check was also successful."
                payment_request.save()

                # Generar PDF y guardar en el directorio media
                pdf_path = generar_pdf_transferencia(payment_request)

                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()

                return HttpResponse(pdf_data, content_type='application/pdf')
            else:
                payment_request.estado = "PDNG"
                payment_request.save()
                return JsonResponse({"detail": "PDNG"}, status=400)
        else:
            return render(request, "dashboard/dashboard.html", {"form": form, "errors": form.errors})

    return render(request, "payments/initiate_payment2.html", {"form": PaymentRequestForm()})