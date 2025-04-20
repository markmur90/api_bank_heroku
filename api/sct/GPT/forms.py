from django import forms
from .models import SepaCreditTransfer


class SepaCreditTransferForm(forms.ModelForm):
    class Meta:
        model = SepaCreditTransfer
        fields = [
            'debtor',
            'debtor_account',
            'creditor',
            'creditor_account',
            'creditor_agent',
            'instructed_amount',
            'purpose_code',
            'requested_execution_date',
            'remittance_information_structured',
            'remittance_information_unstructured',
        ]
        widgets = {
            'requested_execution_date': forms.DateInput(attrs={'type': 'date'}),
        }
