from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from .models import SepaCreditTransfer  # Importar modelo de transferencias SEPA

@require_http_methods(["GET"])
def transfer_detail(request, payment_id):
    """
    Vista de detalle: muestra la información completa de una transferencia SEPA.
    Incluye datos de deudor, acreedor, monto, moneda, fechas (creación, ejecución solicitada), 
    estado actual de la transacción y cualquier identificador asociado.
    """
    transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    # Renderizar una plantilla con el detalle de la transferencia
    return render(request, 'api/GPT/transfer_detail.html', {'transfer': transfer})

@require_http_methods(["GET"])
def confirm_cancel_transfer(request, payment_id):
    """
    Vista de confirmación de cancelación: pide confirmación antes de anular una transferencia SEPA.
    Muestra los detalles de la transferencia a cancelar y un formulario o botones para confirmar o cancelar la acción.
    La acción de cancelación real (cancel_sepa_transfer) se ejecutaría solo si el usuario confirma en esta vista.
    """
    transfer = get_object_or_404(SepaCreditTransfer, payment_id=payment_id)
    # Renderizar una página de confirmación con detalles de la transferencia
    return render(request, 'api/GPT/confirm_cancel.html', {'transfer': transfer})

@require_http_methods(["GET"])
def export_transfers_csv(request):
    """
    Vista de exportación: genera un archivo CSV con todas las transferencias SEPA.
    Recorre los registros de SepaCreditTransfer y escribe filas con campos clave para descarga.
    """
    transfers = SepaCreditTransfer.objects.all().order_by('-created_at')
    # Preparar la respuesta HTTP con contenido CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transfers.csv"'
    # Escribir el encabezado CSV
    writer = csv.writer(response)
    writer.writerow(['Payment ID', 'Debtor Name', 'Creditor Name', 'Amount', 'Currency', 'Status', 'Requested Execution Date'])
    # Escribir cada transferencia como fila en el CSV
    for transfer in transfers:
        writer.writerow([
            str(transfer.payment_id),
            transfer.debtor.debtor_name if transfer.debtor else "",
            transfer.creditor.creditor_name if transfer.creditor else "",
            transfer.instructed_amount.amount if transfer.instructed_amount else "",
            transfer.instructed_amount.currency if transfer.instructed_amount else "",
            transfer.transaction_status,
            transfer.requested_execution_date.strftime("%Y-%m-%d") if transfer.requested_execution_date else ""
        ])
    return response
