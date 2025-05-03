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
    path('bulk/crear/', views.CrearBulkTransferView.as_view(), name='crear_bulk_transferencia'),
    path('bulk/<str:payment_id>/enviar/', views.EnviarBulkTransferView.as_view(), name='enviar_bulk_transferencia'),
    path('bulk/<str:payment_id>/estado/', views.EstadoBulkTransferView.as_view(), name='estado_bulk_transferencia'),
    path('bulk/<str:payment_id>/', views.DetalleBulkTransferView.as_view(), name='detalle_transferencia_bulk'),

    # OTP Retry
    path('<str:payment_id>/otp/', views.retry_second_factor, name='retry_second_factor'),

    # Autenticación admin
    path('login/', LoginView.as_view(template_name='sepa_transferencias/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
]
