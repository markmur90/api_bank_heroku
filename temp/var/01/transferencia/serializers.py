from rest_framework import serializers
from .models import Transferencia

class SwiftTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transferencia
        fields = '__all__'
