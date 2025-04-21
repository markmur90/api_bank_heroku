from django.urls import path
from . import views

urlpatterns = [
    path('', views.fetch_sepa_credit_transfers, name='fetch_sepa_credit_transfers'),
]
