from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from api_swift_db.transactions.models import Transferencia
from django.shortcuts import render, redirect
import requests
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
import os
from config import settings

class TransferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transferencia
        fields = '__all__'

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
            return redirect("transferencia")
        else:
            return render(request, "login.html", {"error": "Credenciales inválidas"})
    return render(request, "login.html")

@login_required
def transferencia_view(request):
    if request.method == "POST":
        origin_iban = request.POST.get("origin_iban")
        origin_bic = request.POST.get("origin_bic")
        amount = request.POST.get("amount")
        currency_code = request.POST.get("currency_code")
        counter_party_bank_name = request.POST.get("counter_party_bank_name")
        counter_party_account_number = request.POST.get("counter_party_account_number")
        counter_party_name = request.POST.get("counter_party_name")
        counter_party_bic = request.POST.get("counter_party_bic")
        payment_reference = request.POST.get("payment_reference")

        # Guardar en la base de datos (ajustar según el modelo de Transferencia)
        transferencia = Transferencia.objects.create(
            usuario=request.user,
            monto=amount,
            estado="pendiente",
            # Ajustar los campos según el modelo de Transferencia
            origin_iban=origin_iban,
            origin_bic=origin_bic,
            currency_code=currency_code,
            counter_party_bank_name=counter_party_bank_name,
            counter_party_account_number=counter_party_account_number,
            counter_party_name=counter_party_name,
            counter_party_bic=counter_party_bic,
            payment_reference=payment_reference,
        )

        # Enviar los datos al banco en formato JSON
        data = [{
            "origin_iban": origin_iban,
            "origin_bic": origin_bic,
            "amount": float(amount),
            "currency_code": currency_code,
            "counter_party_bank_name": counter_party_bank_name,
            "counter_party_account_number": counter_party_account_number,
            "counter_party_name": counter_party_name,
            "counter_party_bic": counter_party_bic,
            "payment_reference": payment_reference,
        }]
        headers = {"Content-Type": "application/json"}
        #response = requests.post("https://api.banco.com/transferencias", json=data, headers=headers)
        response = requests.post("http://127.0.0.1:8082/transferencias", json=data, headers=headers)

        # Actualizar estado si la transferencia fue exitosa
        if response.status_code == 200:
            transferencia.estado = "completado"
            transferencia.save()

            # Generar PDF y guardar en el directorio media
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p.drawString(100, 750, "Transferencia Exitosa")
            p.drawString(100, 730, f"Usuario: {request.user.username}")
            p.drawString(100, 710, f"Monto: {amount} {currency_code}")
            p.drawString(100, 690, f"Destinatario: {counter_party_name}")
            p.drawString(100, 670, f"Referencia de Pago: {payment_reference}")
            p.showPage()
            p.save()

            # Guardar el PDF en el directorio media
            pdf_path = os.path.join(settings.MEDIA_ROOT, f'transferencia_{transferencia.id}.pdf')
            with open(pdf_path, 'wb') as f:
                f.write(buffer.getvalue())

            return HttpResponse(buffer.getvalue(), content_type='application/pdf')

        return redirect("transferencia_exitosa")

    return render(request, "transferencia.html")

@login_required
def transferencia_exitosa_view(request):
    return render(request, "transferencia_exitosa.html")