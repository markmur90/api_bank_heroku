from django.urls import path
from core.transactions.views import CashAccountTransactionList, CashAccountTransactionDetail

urlpatterns = [
    path('transactions/', CashAccountTransactionList.as_view(), name='transaction-list'),
    path('transactions/<str:transactionId>/', CashAccountTransactionDetail.as_view(), name='transaction-detail'),
]