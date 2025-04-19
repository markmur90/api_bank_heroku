from django.urls import path
from . import views

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate_payment'),
    path('status/<str:payment_id>/', views.check_payment_status, name='check_payment_status'),
    path('reachability/<str:iban>/', views.check_iban_reachability, name='check_iban_reachability'),
    path('otp/', views.get_otp, name='get_otp'),
    path('load_data/', views.load_data, name='load_data'),
    path('load_currency_code/', views.load_currency_code, name='load_currency_code'),
    path('load_iban/', views.load_iban, name='load_iban'),
    path('load_account_reference/', views.load_account_reference, name='load_account_reference'),
    path('load_amount/', views.load_amount, name='load_amount'),
    path('load_address/', views.load_address, name='load_address'),
    path('data_loaded_success/', views.data_loaded_success, name='data_loaded_success'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
