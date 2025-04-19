from rest_framework import serializers
from .models import SepaCreditTransfer, Debtor, Creditor, Account, InstructedAmount, Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"

class DebtorSerializer(serializers.ModelSerializer):
    postal_address = AddressSerializer()

    class Meta:
        model = Debtor
        fields = "__all__"

class CreditorSerializer(serializers.ModelSerializer):
    postal_address = AddressSerializer()

    class Meta:
        model = Creditor
        fields = "__all__"

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"

class InstructedAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructedAmount
        fields = "__all__"

class SepaCreditTransferSerializer(serializers.ModelSerializer):
    debtor = DebtorSerializer()
    debtor_account = AccountSerializer()
    creditor = CreditorSerializer()
    creditor_account = AccountSerializer()
    instructed_amount = InstructedAmountSerializer()

    class Meta:
        model = SepaCreditTransfer
        fields = "__all__"
