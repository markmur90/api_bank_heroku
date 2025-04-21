from django.urls import path
from . import views

urlpatterns = [
    # Iniciar transferencia
    path('transfer/initiate/', views.initiate_sepa_transfer, name='initiate_transferGPT'),

    # Ver estado
    path('transfer/<uuid:payment_id>/status/', views.check_transfer_status, name='check_statusGPT'),

    # Listado general
    path('transfer/list/', views.transfer_list_view, name='transfer_listGPT'),

    # Eliminar transferencia
    path('transfer/<uuid:payment_id>/delete/', views.delete_transfer, name='delete_transferGPT'),

    # Descargar PDF
    path('transfer/<uuid:payment_id>/pdf/', views.generate_transfer_pdf, name='generate_transfer_pdfGPT'),

    # 🔁 Cancelar transferencia (DELETE)
    path('transfer/<uuid:payment_id>/cancel/', views.cancel_sepa_transfer, name='cancel_transferGPT'),

    # 🔁 Retry segundo factor TAN (PATCH)
    path('transfer/<uuid:payment_id>/retry-auth/', views.retry_sepa_transfer_auth, name='retry_transfer_authGPT'),
]

