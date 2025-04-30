import os
import json
import uuid
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests

from .models import Transferencia
from .forms import TransferenciaForm
from .utils import generar_xml_pain_001, validar_xml_contra_schema, handle_error_response

logger = logging.getLogger(__name__)

def send_transfer_view2(request):
    if request.method == "POST":
        form = TransferenciaForm(request.POST)
        if form.is_valid():
            transferencia = form.save(commit=False)
            transferencia.payment_id = str(uuid.uuid4())
            transferencia.save()

            # Preparar datos y cabeceras
            request_data = transferencia.to_api_payload()
            otp_method = request.POST.get("otp_method", "PUSHTAN")  # Puede venir del formulario
            otp = "PUSHTAN" if otp_method == "PUSHTAN" else request.POST.get("otp_code", "")

            headers = {
                "Authorization": f"Bearer {settings.DBAPI_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "idempotency-id": str(uuid.uuid4()),
                "otp": otp,
                "Correlation-Id": str(uuid.uuid4()),
            }

            # Generar XML
            xml_file = generar_xml_pain_001(transferencia)
            try:
                validar_xml_contra_schema(xml_file, "schemas/pain.001.xsd")
            except Exception as e:
                messages.error(request, f"Error al validar XML: {str(e)}")
                return render(request, "enviar_transferencia.html", {"form": form})

            # Enviar a la API
            url = "https://simulator-api.db.com:443/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"
            try:
                response = requests.post(url, headers=headers, json=request_data)
            except requests.RequestException as e:
                logger.exception("Error de conexión al enviar la transferencia")
                messages.error(request, "No se pudo conectar con el banco. Intente más tarde.")
                return render(request, "enviar_transferencia.html", {"form": form})

            # Crear log
            log_file_path = f"logs/transferencias/transferencia_{transferencia.payment_id}.log"
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            with open(log_file_path, "a", encoding="utf-8") as log_file:
                log_file.write("=== SOLICITUD ===\n")
                log_file.write(json.dumps(request_data, indent=2, ensure_ascii=False) + "\n")
                log_file.write("=== CABECERAS ===\n")
                log_file.write(json.dumps(headers, indent=2, ensure_ascii=False) + "\n")
                log_file.write(f"=== RESPUESTA {response.status_code} ===\n")
                log_file.write(response.text + "\n")
                log_file.write("=== CABECERAS RESPUESTA ===\n")
                log_file.write(json.dumps(dict(response.headers), indent=2, ensure_ascii=False) + "\n")

            # Procesar respuesta
            if response.status_code == 201:
                respuesta_json = response.json()
                transferencia.estado = respuesta_json.get("transactionStatus", "PDNG")
                transferencia.payment_id = respuesta_json.get("paymentId", transferencia.payment_id)
                transferencia.auth_id = respuesta_json.get("authId")
                transferencia.save()
                messages.success(request, "Transferencia enviada correctamente.")
                return redirect("detalle_transferencia", transferencia.id)
            else:
                handle_error_response(response, logger)
                messages.error(request, "Error al enviar la transferencia. Revisa el log para más detalles.")
                return render(request, "enviar_transferencia.html", {"form": form})

        else:
            messages.error(request, "Corrige los errores del formulario.")
    else:
        form = TransferenciaForm()
    return render(request, "enviar_transferencia.html", {"form": form})
