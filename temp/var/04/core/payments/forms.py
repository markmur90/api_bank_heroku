from django import forms
from .models import PaymentRequest, AccountReference, Amount, Address, CurrencyCode, IBAN
from django_select2.forms import Select2Widget

# class PaymentRequestForm(forms.ModelForm):
#     class Meta:
#         model = PaymentRequest
#         fields = [
#             'creditor_account',
#             'creditor_address',
#             'creditor_agent',
#             'creditor_name',
#             'debtor_account',
#             'end_to_end_identification',
#             'instructed_amount',
#             'remittance_information_unstructured'
#         ]
#         widgets = {
#             'creditor_account': Select2Widget,
#             'creditor_address': Select2Widget,
#             'debtor_account': Select2Widget,
#             'instructed_amount': Select2Widget,
#         }
class PaymentRequestForm(forms.ModelForm):
    class Meta:
        model = PaymentRequest
        fields = [
            'creditor_name', 'creditor_account', 'creditor_bank', 'creditor_address', 'creditor_agent',
            'debtor_name', 'debtor_account', 'debtor_bank', 'debtor_address', 'debtor_agent',
            'end_to_end_identification', 'instructed_amount', 'remittance_information_unstructured'
        ]
        widgets = {
            'creditor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'creditor_account': Select2Widget,
            'creditor_bank': forms.TextInput(attrs={'class': 'form-control'}),
            'creditor_agent': forms.TextInput(attrs={'class': 'form-control'}),
            'debtor_agent': forms.TextInput(attrs={'class': 'form-control'}),
            'creditor_address': Select2Widget,
            'debtor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'debtor_account': Select2Widget,
            'debtor_bank': forms.TextInput(attrs={'class': 'form-control'}),
            'debtor_address': Select2Widget,
            'end_to_end_identification': forms.TextInput(attrs={'class': 'form-control'}),            
            # 'payment_id': forms.TextInput(attrs={'class': 'form-control'}),
            'instructed_amount': Select2Widget,
            'remittance_information_unstructured': forms.TextInput(attrs={'class': 'form-control'}),
        }

class PaymentRequest2Form(forms.ModelForm):
    class Meta:
        model = PaymentRequest
        fields = [
            'creditor_name', 'creditor_account', 'creditor_bank', 'creditor_address', 'creditor_agent',
            'debtor_name', 'debtor_account', 'debtor_bank', 'debtor_address', 'debtor_agent',
            'end_to_end_identification', 'instructed_amount', 'remittance_information_unstructured'
        ]
        widgets = {
            'creditor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'creditor_account': Select2Widget,
            'creditor_bank': forms.TextInput(attrs={'class': 'form-control'}),
            'creditor_agent': forms.TextInput(attrs={'class': 'form-control'}),
            'debtor_agent': forms.TextInput(attrs={'class': 'form-control'}),
            'creditor_address': Select2Widget,
            'debtor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'debtor_account': Select2Widget,
            'debtor_bank': forms.TextInput(attrs={'class': 'form-control'}),
            'debtor_address': Select2Widget,
            'end_to_end_identification': forms.TextInput(attrs={'class': 'form-control'}),            
            'instructed_amount': Select2Widget,
            'remittance_information_unstructured': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
class AccountReferenceForm(forms.ModelForm):
    class Meta:
        model = AccountReference
        fields = ['currency_code', 'iban', 'swift']
        widgets = {
            'currency_code': Select2Widget,
            'iban': Select2Widget,
            'swift': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AmountForm(forms.ModelForm):
    class Meta:
        model = Amount
        fields = ['currency_code', 'amount']
        widgets = {
            'currency_code': Select2Widget,
        }

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['building_number', 'city', 'country', 'postal_code', 'street']
        widgets = {
            'building_number': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'street': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CurrencyCodeForm(forms.ModelForm):
    class Meta:
        model = CurrencyCode
        fields = ['currency_code']
        widgets = {
            'currency_code': Select2Widget,
        }
 
class IBANForm(forms.ModelForm):
    class Meta:
        model = IBAN
        fields = ['iban']
        widgets = {
            'iban': Select2Widget,
        }
