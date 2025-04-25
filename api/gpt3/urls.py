from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # Transferencias individuales
    path('', views.listar_transferencias, name='listar_transferencias'),
    path('crear/', views.crear_transferencia, name='crear_transferencia'),
    path('<str:payment_id>/', views.detalle_transferencia, name='detalle_transferencia'),
    path('<str:payment_id>/enviar/', views.enviar_transferencia, name='enviar_transferencia'),
    path('<str:payment_id>/estado/', views.estado_transferencia, name='estado_transferencia'),
    path('<str:payment_id>/pdf/', views.descargar_pdf, name='descargar_pdf'),

    # Transferencias masivas
    path('bulk/crear/', views.CrearBulkTransferView, name='crear_bulk_transferencia'),
    path('bulk/<str:payment_id>/enviar/', views.EnviarBulkTransferView, name='enviar_bulk_transferencia'),
    path('bulk/<str:payment_id>/estado/', views.EstadoBulkTransferView, name='estado_bulk_transferencia'),
    path('bulk/<str:payment_id>/', views.DetalleBulkTransferView, name='detalle_transferencia_bulk'),

    # OTP Retry
    path('<str:payment_id>/otp/', views.retry_second_factor, name='retry_second_factor'),
]
