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

    # Crear
    path('create/account/', views.create_account, name='create_accountGPT3'),
    path('create/amount/', views.create_amount, name='create_amountGPT3'),
    path('create/financial-institution/', views.create_financial_institution, name='create_financial_institutionGPT3'),
    path('create/postal-address/', views.create_postal_address, name='create_postal_addressGPT3'),
    path('create/debtor/', views.create_debtor, name='create_debtorGPT3'),
    path('create/creditor/', views.create_creditor, name='create_creditorGPT3'),
    
    # Listados
    path('list/postal-address/', views.postal_address_list_view, name='postal_address_listGPT3'),
    path('list/debtor/', views.debtor_list_view, name='debtor_listGPT3'),
    path('list/creditor/', views.creditor_list_view, name='creditor_listGPT3'),
    path('list/account/', views.account_list_view, name='account_listGPT3'),
    path('list/financial-institution/', views.financial_institution_list_view, name='financial_institution_listGPT3'),
    path('list/amount/', views.amount_list_view, name='amount_listGPT3'),
]
