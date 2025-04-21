# apps/sepa_payment/views.py
import requests
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .forms import SepaCreditTransferForm
from .models import SepaCreditTransfer
from .services import SepaPaymentService

def index(request):
    return render(request, 'sepa_payment/base.html')

@require_http_methods(['GET', 'POST'])
def create_transfer(request):
    if request.method == 'POST':
        form = SepaCreditTransferForm(request.POST)
        if form.is_valid():
            try:
                # Crear la transferencia
                service = SepaPaymentService()
                payment_id = service.create_payment(form.cleaned_data)
                
                # Guardar en la base de datos
                transfer = form.save(commit=False)
                transfer.payment_id = payment_id
                transfer.save()
                
                messages.success(request, 'Transferencia creada exitosamente')
                return redirect('transfer_status', payment_id=payment_id)
            except Exception as e:
                messages.error(request, f'Error al crear la transferencia: {str(e)}')
                return render(request, 'sepa_payment/transfer.html', {'form': form})
    else:
        form = SepaCreditTransferForm()
    
    return render(request, 'sepa_payment/transfer.html', {'form': form})


# def transfer_status(request, payment_id):
#     try:
#         transfer = SepaCreditTransfer.objects.get(payment_id=payment_id)
#         service = SepaPaymentService()
#         status = service.get_payment_status(payment_id)
#         return render(request, 'sepa_payment/status.html', {
#             'transfer': transfer,
#             'status': status
#         })
#     except SepaCreditTransfer.DoesNotExist:
#         messages.error(request, 'Transferencia no encontrada')
#         return redirect('index')


# apps/sepa_payment/views.py
def transfer_status(request, payment_id):
    try:
        transfer = SepaCreditTransfer.objects.get(payment_id=payment_id)
        service = SepaPaymentService()
        
        # Obtener el estado más reciente
        latest_status = transfer.status_history.latest('timestamp')
        
        # Obtener todos los estados para el historial
        status_history = transfer.status_history.all().order('-timestamp')
        
        return render(request, 'sepa_payment/status.html', {
            'transfer': transfer,
            'latest_status': latest_status,
            'status_history': status_history,
            'errors': transfer.errors.all()
        })
    except SepaCreditTransfer.DoesNotExist:
        messages.error(request, 'Transferencia no encontrada')
        return redirect('index')