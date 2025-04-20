from django import forms
from .models import (
    SepaCreditTransfer, Party, Account, Amount,
    FinancialInstitution, PostalAddress, PaymentIdentification
)


class SepaCreditTransferForm(forms.ModelForm):
    class Meta:
        model = SepaCreditTransfer
        fields = [
            'debtor', 'debtor_account', 'creditor', 'creditor_account',
            'creditor_agent', 'instructed_amount', 'purpose_code',
            'requested_execution_date', 'remittance_information_structured',
            'remittance_information_unstructured'
        ]
        widgets = {
            'requested_execution_date': forms.DateInput(attrs={'type': 'date'}),
        }


class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = ['debtor_name', 'creditor_name', 'debtor_postal_address', 'creditor_postal_address']


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['iban', 'currency']


class AmountForm(forms.ModelForm):
    class Meta:
        model = Amount
        fields = ['amount', 'currency']


class FinancialInstitutionForm(forms.ModelForm):
    class Meta:
        model = FinancialInstitution
        fields = ['financial_institution_id']


class PostalAddressForm(forms.ModelForm):
    class Meta:
        model = PostalAddress
        fields = ['country', 'zip_code_and_city', 'street_and_house_number']


class PaymentIdentificationForm(forms.ModelForm):
    class Meta:
        model = PaymentIdentification
        fields = ['end_to_end_id', 'instruction_id']
