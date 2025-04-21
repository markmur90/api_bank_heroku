# apps/sepa_payment/forms.py
from django import forms
from .models import SepaCreditTransfer
from django.core.validators import RegexValidator

class SepaCreditTransferForm(forms.ModelForm):
    class Meta:
        model = SepaCreditTransfer
        fields = [
            'purpose_code',
            'requested_execution_date',
            'debtor_name',
            'debtor_iban',
            'debtor_currency',
            'creditor_name',
            'creditor_iban',
            'creditor_currency',
            'amount',
            'end_to_end_id',
            'instruction_id',
            'remittance_structured',
            'remittance_unstructured',
            'debtor_address_country',
            'debtor_address_street',
            'debtor_address_zip',
            'creditor_address_country',
            'creditor_address_street',
            'creditor_address_zip',
            'creditor_agent_id'
        ]
        widgets = {
            'requested_execution_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})