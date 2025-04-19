from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from config import settings
from api_db_swift.config import BANCO_ORIGEN  # Importar el nombre del banco origen desde la configuración

def generar_pdf_transferencia(transferencia):
    """
    Genera un PDF con los detalles de la transacción.
    """
    # Nombre del archivo PDF
    pdf_filename = f"transferencia_{transferencia.id}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_filename)

    # Crear el PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    
    # Título
    c.drawString(200, 750, "Comprobante de Transferencia SWIFT")

    # Detalles de la transferencia
    detalles = [
        f"Referencia: {transferencia.payment_reference}",
        f"Banco Origen: {BANCO_ORIGEN}",  # Usar el nombre del banco origen desde la configuración
        f"SWIFT Origen: {transferencia.origin_bic}",
        f"Cuenta Origen: {transferencia.origin_iban}",
        f"Número de Cuenta Origen: {transferencia.origin_account_number}",  # Nuevo detalle
        f"Nombre del Propietario de la Cuenta Origen: {transferencia.origin_account_holder_name}",  # Nuevo detalle
        f"Banco Destino: {transferencia.counter_party_bank_name}",
        f"SWIFT Destino: {transferencia.counter_party_bic}",
        f"Cuenta Destino: {transferencia.counter_party_account_number}",
        f"Beneficiario: {transferencia.counter_party_name}",
        f"Monto: {transferencia.monto} {transferencia.currency_code}",
        f"Estado: {transferencia.estado}",
        f"ID Transacción SWIFT: {transferencia.swift_transaction_id}",  # Usar el ID de transacción SWIFT
    ]

    y = 720
    for detalle in detalles:
        c.drawString(100, y, detalle)
        y -= 20

    c.save()
    return pdf_path