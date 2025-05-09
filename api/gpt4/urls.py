from django.urls import path
from api.gpt4 import views

urlpatterns = [
    # Debtor
    path('debtors/create/', views.create_debtor, name='create_debtorGPT4'),
    path('debtors/', views.list_debtors, name='list_debtorsGPT4'),
    
    path('debtor-accounts/create/', views.create_debtor_account, name='create_debtor_accountGPT4'),
    path('debtor-accounts/', views.list_debtor_accounts, name='list_debtor_accountsGPT4'),

    # Creditor
    path('creditors/create/', views.create_creditor, name='create_creditorGPT4'),
    path('creditors/', views.list_creditors, name='list_creditorsGPT4'),
    
    path('creditor-accounts/create/', views.create_creditor_account, name='create_creditor_accountGPT4'),
    path('creditor-accounts/', views.list_creditor_accounts, name='list_creditor_accountsGPT4'),
    
    path('creditor-agents/create/', views.create_creditor_agent, name='create_creditor_agentGPT4'),
    path('creditor-agents/', views.list_creditor_agents, name='list_creditor_agentsGPT4'),

    path('clientids/create/', views.create_clientid, name='create_clientidGPT4'),
    path('kids/create/', views.create_kid, name='create_kidGPT4'),

    # Transfers
    # path('transfers/create/', views.create_transfer, name='create_transferGPT4'),
    # path('transfers/', views.list_transfers, name='list_transfersGPT4'),
    # path('transfers/<int:transfer_id>/', views.transfer_detail, name='transfer_detailGPT4'),
    # path('transfers/<int:transfer_id>/send/', views.send_transfer_view, name='send_transfer_viewGPT4'),
    # path('transfer/<str:payment_id>/sca/', views.transfer_update_sca, name='transfer_update_scaGPT4'),
    
    
    path('transfers/<str:payment_id>/pdf/', views.descargar_pdf, name='descargar_pdfGPT4'),

    path("transfers/<str:payment_id>/edit/", views.edit_transfer, name="edit_transferGPT4"),
    path("transfers/create/", views.create_transfer, name="create_transferGPT4"),
    # path("transfers/<str:payment_id>/send/", views.send_transfer_view, name="send_transfer_viewGPT4"),
    path("transfers/<str:payment_id>/send/", views.send_transfer_view4, name="send_transfer_viewGPT4"),
    path("transfers/<str:payment_id>/sca/", views.transfer_update_sca, name="transfer_update_scaGPT4"),
    path("transfers/<str:payment_id>/", views.transfer_detail, name="transfer_detailGPT4"),
    
    path('oauth2/authorize/', views.oauth2_authorize, name='oauth2_authorize'),
    path('oauth2/callback/', views.oauth2_callback, name='oauth2_callback'),
    path('toggle-oauth/', views.toggle_oauth, name='toggle_oauth'),
    
]