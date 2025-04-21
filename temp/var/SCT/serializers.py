from rest_framework import serializers
from .models import (
    Address, AddressLine, Creditor, CreditorAccount, CreditorAgent, Debtor,
    DebtorAccount, DebtorName, ErrorResponse, InstructedAmount, PaymentIdentification,
    SepaCreditTransferRequest, SepaCreditTransferUpdateScaRequest, SepaCreditTransferResponse,
    SepaCreditTransferDetailsResponse
)

class AddressLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressLine
        fields = ['street_and_house_number', 'zip_code_and_city']

class AddressSerializer(serializers.ModelSerializer):
    address_line = AddressLineSerializer()

    class Meta:
        model = Address
        fields = ['country', 'address_line']

class DebtorNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtorName
        fields = ['name']

class DebtorSerializer(serializers.ModelSerializer):
    postal_address = AddressSerializer()

    class Meta:
        model = Debtor
        fields = ['name', 'postal_address']

class DebtorAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebtorAccount
        fields = ['iban', 'currency']

class CreditorSerializer(serializers.ModelSerializer):
    postal_address = AddressSerializer()

    class Meta:
        model = Creditor
        fields = ['name', 'postal_address']

class CreditorAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditorAccount
        fields = ['iban', 'currency']

class CreditorAgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditorAgent
        fields = ['financial_institution_id']

class PaymentIdentificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentIdentification
        fields = ['end_to_end_id', 'instruction_id']

class InstructedAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructedAmount
        fields = ['amount', 'currency']

class SepaCreditTransferRequestSerializer(serializers.ModelSerializer):
    debtor = DebtorSerializer()
    debtor_account = DebtorAccountSerializer()
    payment_identification = PaymentIdentificationSerializer()
    instructed_amount = InstructedAmountSerializer()
    creditor_agent = CreditorAgentSerializer()
    creditor = CreditorSerializer()
    creditor_account = CreditorAccountSerializer()

    class Meta:
        model = SepaCreditTransferRequest
        fields = [
            'purpose_code', 'requested_execution_date', 'debtor', 'debtor_account',
            'payment_identification', 'instructed_amount', 'creditor_agent', 'creditor',
            'creditor_account', 'remittance_information_structured', 'remittance_information_unstructured'
        ]

class SepaCreditTransferUpdateScaRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SepaCreditTransferUpdateScaRequest
        fields = ['action', 'auth_id']

class SepaCreditTransferResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SepaCreditTransferResponse
        fields = ['transaction_status', 'payment_id', 'auth_id']

class SepaCreditTransferDetailsResponseSerializer(serializers.ModelSerializer):
    debtor = DebtorSerializer()
    debtor_account = DebtorAccountSerializer()
    payment_identification = PaymentIdentificationSerializer()
    instructed_amount = InstructedAmountSerializer()
    creditor_agent = CreditorAgentSerializer()
    creditor = CreditorSerializer()
    creditor_account = CreditorAccountSerializer()

    class Meta:
        model = SepaCreditTransferDetailsResponse
        fields = [
            'transaction_status', 'payment_id', 'purpose_code', 'requested_execution_date',
            'debtor', 'debtor_account', 'creditor_agent', 'creditor', 'creditor_account',
            'payment_identification', 'instructed_amount', 'remittance_information_structured',
            'remittance_information_unstructured'
        ]

class ErrorResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErrorResponse
        fields = ['code', 'message', 'message_id']
