# apps/sepa_payment/urls.py
from django.urls import path
from . import views

app_name = 'sepa_payment'

urlpatterns = [
    path('', views.index, name='index'),
    path('transfer/', views.create_transfer, name='create_transfer'),
    path('transfer/<str:payment_id>/status/', views.transfer_status, name='transfer_status'),
]