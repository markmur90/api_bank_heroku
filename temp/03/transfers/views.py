from django.http import FileResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import TransferenciaSWIFT
from .services import enviar_transferencia_swift, simular_respuesta_swift, generar_pdf_transferencia
import uuid
import os
 
@api_view(['GET'])
def obtener_datos(request):
    data = {
        "ip": "193.150.166.0",
        "organización": "Deutsche Bank AG",
        "ubicación": "Frankfurt, Alemania"
    }
    return Response(data)

@api_view(['POST'])
def realizar_transferencia(request):
    try:
        data = request.data
        monto = data.get("monto")
        
        if not monto or float(monto) <= 0:
            return Response({"error": "Monto inválido"}, status=400)
        
        referencia = str(uuid.uuid4())[:12]  # Generar un número de referencia único

        transferencia = TransferenciaSWIFT.objects.create(
            monto=monto,
            referencia=referencia
        )
        
        return Response({
            "mensaje": "Transferencia creada exitosamente",
            "referencia": transferencia.referencia,
            "monto": transferencia.monto,
            "estado": transferencia.estado
        }, status=201)
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # 🔐 Solo usuarios autenticados pueden acceder
def realizar_transferencia_simulada(request):
    data = request.data

    # Validar datos obligatorios
    required_fields = ["banco_destino", "codigo_swift_destino", "numero_cuenta_destino", "nombre_beneficiario", "monto"]
    for field in required_fields:
        if field not in data or not data[field]:
            return Response({"error": f"Falta el campo obligatorio: {field}"}, status=400)

    monto = float(data["monto"])
    if monto <= 0:
        return Response({"error": "El monto debe ser mayor a 0"}, status=400)

    referencia = str(uuid.uuid4())[:12]

    # Crear un registro en la base de datos
    transferencia = TransferenciaSWIFT.objects.create(
        banco_destino=data["banco_destino"],
        codigo_swift_destino=data["codigo_swift_destino"],
        numero_cuenta_destino=data["numero_cuenta_destino"],
        nombre_beneficiario=data["nombre_beneficiario"],
        monto=monto,
        referencia=referencia
    )

    # Simular respuesta de SWIFT
    resultado = simular_respuesta_swift(referencia, monto)

    # Actualizar estado en la base de datos
    transferencia.estado = resultado["estado"]
    transferencia.save()

    # Generar el PDF
    pdf_path = generar_pdf_transferencia(transferencia)

    return Response({
        "mensaje": "Transferencia simulada",
        "referencia": referencia,
        "estado": transferencia.estado,
        "swift_transaction_id": resultado["swift_transaction_id"],
        "pdf_url": f"/api/descargar-pdf/{transferencia.referencia}/"
    }, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # 🔐 Solo usuarios autenticados pueden acceder
def realizar_transferencia_real(request):
    try:
        data = request.data

        # ✅ Validar que todos los datos estén presentes
        required_fields = ["banco_destino", "codigo_swift_destino", "numero_cuenta_destino", "nombre_beneficiario", "monto"]
        for field in required_fields:
            if field not in data or not data[field]:
                return Response({"error": f"Falta el campo obligatorio: {field}"}, status=400)

        # ✅ Validar monto
        try:
            monto = float(data["monto"])
            if monto <= 0:
                return Response({"error": "El monto debe ser mayor a 0"}, status=400)
        except ValueError:
            return Response({"error": "El monto debe ser un número válido"}, status=400)

        referencia = str(uuid.uuid4())[:12]

        # ✅ Crear registro en la base de datos
        transferencia = TransferenciaSWIFT.objects.create(
            banco_destino=data["banco_destino"],
            codigo_swift_destino=data["codigo_swift_destino"],
            numero_cuenta_destino=data["numero_cuenta_destino"],
            nombre_beneficiario=data["nombre_beneficiario"],
            monto=monto,
            referencia=referencia
        )

        # ✅ Enviar la transferencia real a SWIFT
        try:
            resultado = enviar_transferencia_swift({
                "banco_origen": transferencia.banco_origen,
                "codigo_swift_origen": transferencia.codigo_swift_origen,
                "numero_cuenta_origen": transferencia.numero_cuenta_origen,
                "nombre_origen": transferencia.nombre_origen,

                "banco_destino": transferencia.banco_destino,
                "codigo_swift_destino": transferencia.codigo_swift_destino,
                "numero_cuenta_destino": transferencia.numero_cuenta_destino,
                "nombre_beneficiario": transferencia.nombre_beneficiario,

                "moneda": transferencia.moneda,
                "monto": transferencia.monto,
                "referencia": transferencia.referencia
            })
            transferencia.estado = "Completada" if "error" not in resultado else "Fallida"
        except Exception as e:
            transferencia.estado = "Error"
            transferencia.save()
            return Response({"error": f"Error en la transferencia: {str(e)}"}, status=500)

        transferencia.save()

        # ✅ Generar el PDF (manejo de errores)
        try:
            pdf_path = generar_pdf_transferencia(transferencia)
        except Exception as e:
            pdf_path = None
            print(f"Error generando PDF: {str(e)}")

        response_data = {
            "mensaje": "Transferencia procesada",
            "referencia": referencia,
            "estado": transferencia.estado,
            "resultado": resultado,
        }

        if pdf_path:
            response_data["pdf_url"] = f"/media/{os.path.basename(pdf_path)}"

        return Response(response_data, status=200)
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def descargar_pdf(request, referencia):
    """
    Descarga el PDF de una transferencia específica.
    """
    pdf_path = os.path.join("media", f"transferencia_{referencia}.pdf")

    if os.path.exists(pdf_path):
        return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf')
    else:
        return Response({"error": "Archivo no encontrado"}, status=404)