from django.urls import path
from api.gpt3 import views2

urlpatterns = [
    # Transferencias individuales
    path('', views2.listar_transferencias, name='listar_transferenciasGPT3'),
    path('crear/', views2.crear_transferencia, name='crear_transferenciaGPT3'),
    path('detalle/<str:payment_id>/', views2.detalle_transferencia, name='detalle_transferenciaGPT3'),
    path('descargar-pdf/<str:payment_id>/', views2.descargar_pdf, name='descargar_pdfGPT3'),
    path('ver-log/<str:payment_id>/', views2.ver_log_transferencia, name='ver_log_transferenciaGPT3'),
    path('enviar/<str:payment_id>/', views2.enviar_transferencia, name='enviar_transferenciaGPT3'),
    path('estado/<str:payment_id>/', views2.estado_transferencia, name='estado_transferenciaGPT3'),
    path('cancelar/<str:payment_id>/', views2.cancelar_transferencia, name='cancelar_transferenciaGPT3'),
    path('retry-2fa/<str:payment_id>/', views2.retry_second_factor_view, name='retry_second_factorGPT3'),

    # Transferencias masivas (bulk)
    path('bulk/crear/', views2.CrearBulkTransferView, name='crear_bulk_transferGPT3'),
    path('bulk/enviar/<str:payment_id>/', views2.EnviarBulkTransferView, name='enviar_bulk_transferGPT3'),
    path('bulk/estado/<str:payment_id>/', views2.EstadoBulkTransferView, name='estado_bulk_transferGPT3'),
    path('bulk/detalle/<str:payment_id>/', views2.DetalleBulkTransferView, name='detalle_transferencia_bulkGPT3'),

    # Listados de entidades auxiliares
    path('debtors/', views2.debtor_list_view, name='debtor_listGPT3'),
    path('creditors/', views2.creditor_list_view, name='creditor_listGPT3'),
    path('accounts/', views2.account_list_view, name='account_listGPT3'),
    path('addresses/', views2.postal_address_list_view, name='postal_address_listGPT3'),
    path('institutions/', views2.financial_institution_list_view, name='financial_institution_listGPT3'),
    path('amounts/', views2.amount_list_view, name='amount_listGPT3'),

    # Creación de entidades auxiliares
    path('crear-account/', views2.create_account, name='create_accountGPT3'),
    path('crear-amount/', views2.create_amount, name='create_amountGPT3'),
    path('crear-institution/', views2.create_financial_institution, name='create_financial_institutionGPT3'),
    path('crear-address/', views2.create_postal_address, name='create_postal_addressGPT3'),
    path('crear-payment-identification/', views2.create_payment_identification, name='create_payment_identificationGPT3'),
    path('crear-debtor/', views2.create_debtor, name='create_debtorGPT3'),
    path('crear-creditor/', views2.create_creditor, name='create_creditorGPT3'),
]
