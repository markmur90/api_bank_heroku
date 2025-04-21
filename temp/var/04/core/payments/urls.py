from django.urls import path
from . import views

urlpatterns = [
    path('initiate_payment/', views.initiate_payment, name='initiate_payment'),
    path('initiate_payment2/', views.initiate_payment2, name='initiate_payment2'),
    path('initiate_payment3/', views.initiate_payment3, name='initiate_payment3'),
    path('generate_token/', views.generate_token, name='generate_token'),
    path('check_payment_status/<str:payment_id>/', views.check_payment_status, name='check_payment_status'),
    path('check_iban_reachability/<str:iban>/', views.check_iban_reachability, name='check_iban_reachability'),
    path('load_data/', views.load_data, name='load_data'),
    path('load_currency_code/', views.load_currency_code, name='load_currency_code'),
    path('load_iban/', views.load_iban, name='load_iban'),
    path('load_account_reference/', views.load_account_reference, name='load_account_reference'),
    path('load_amount/', views.load_amount, name='load_amount'),
    path('load_address/', views.load_address, name='load_address'),
    path('data_loaded_success/', views.data_loaded_success, name='data_loaded_success'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
