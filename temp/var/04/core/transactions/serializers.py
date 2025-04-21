from rest_framework import serializers
from core.transactions.models import CashAccountTransaction

class CashAccountTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashAccountTransaction
        fields = '__all__'