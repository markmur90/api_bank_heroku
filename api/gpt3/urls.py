from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from api.gpt3.views import *

urlpatterns = [
    # Transferencias individuales
    path('', listar_transferencias, name='listar_transferencias'),
    path('crear/', crear_transferencia, name='crear_transferencia'),
    path('<str:payment_id>/', detalle_transferencia, name='detalle_transferencia'),
    path('<str:payment_id>/enviar/', enviar_transferencia, name='enviar_transferencia'),
    path('<str:payment_id>/estado/', estado_transferencia, name='estado_transferencia'),
    path('<str:payment_id>/pdf/', descargar_pdf, name='descargar_pdf'),

    # Transferencias masivas
    path('bulk/crear/', CrearBulkTransferView, name='crear_bulk_transferencia'),
    path('bulk/<str:payment_id>/enviar/', EnviarBulkTransferView, name='enviar_bulk_transferencia'),
    path('bulk/<str:payment_id>/estado/', EstadoBulkTransferView, name='estado_bulk_transferencia'),
    path('bulk/<str:payment_id>/', DetalleBulkTransferView, name='detalle_transferencia_bulk'),

    # OTP Retry
    path('<str:payment_id>/otp/', retry_second_factor, name='retry_second_factor'),

    # Crear
    path('create/account/', create_account, name='create_accountGPT3'),
    path('create/amount/', create_amount, name='create_amountGPT3'),
    path('create/financial-institution/', create_financial_institution, name='create_financial_institutionGPT3'),
    path('create/postal-address/', create_postal_address, name='create_postal_addressGPT3'),
    path('create/debtor/', create_debtor, name='create_debtorGPT3'),
    path('create/creditor/', create_creditor, name='create_creditorGPT3'),
    
    # Listados
    path('list/postal-address/', postal_address_list_view, name='postal_address_listGPT3'),
    path('list/debtor/', debtor_list_view, name='debtor_listGPT3'),
    path('list/creditor/', creditor_list_view, name='creditor_listGPT3'),
    path('list/account/', account_list_view, name='account_listGPT3'),
    path('list/financial-institution/', financial_institution_list_view, name='financial_institution_listGPT3'),
    path('list/amount/', amount_list_view, name='amount_listGPT3'),
]
