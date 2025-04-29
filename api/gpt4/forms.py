from datetime import datetime
from django import forms
import pytz
from api.gpt4.models import Debtor, DebtorAccount, Creditor, CreditorAccount, CreditorAgent, PaymentTypeInformation, Transfer

class DebtorForm(forms.ModelForm):
    class Meta:
        model = Debtor
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_id': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_street': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_city': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DebtorAccountForm(forms.ModelForm):
    class Meta:
        model = DebtorAccount
        fields = '__all__'
        widgets = {
            'debtor': forms.Select(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CreditorForm(forms.ModelForm):
    class Meta:
        model = Creditor
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_street': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_address_city': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CreditorAccountForm(forms.ModelForm):
    class Meta:
        model = CreditorAccount
        fields = '__all__'
        widgets = {
            'creditor': forms.Select(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CreditorAgentForm(forms.ModelForm):
    class Meta:
        model = CreditorAgent
        fields = '__all__'
        widgets = {
            'bic': forms.TextInput(attrs={'class': 'form-control'}),
            'financial_institution_id': forms.TextInput(attrs={'class': 'form-control'}),
            'other_information': forms.TextInput(attrs={'class': 'form-control'}),
        }

class TransferForm(forms.ModelForm):
    # Nuevos campos manuales para PaymentTypeInformation
    payment_type_information_service_level = forms.CharField(
        required=False,
        max_length=10,
        label="Nivel de Servicio (Service Level Code)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'INST'})
    )
    payment_type_information_local_instrument = forms.CharField(
        required=False,
        max_length=35,
        label="Instrumento Local (Local Instrument Code)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'INST'})
    )
    payment_type_information_category_purpose = forms.CharField(
        required=False,
        max_length=35,
        label="Propósito de Categoría (Category Purpose Code)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GDSV'})
    )

    class Meta:
        model = Transfer
        fields = [
            'debtor', 'debtor_account', 'creditor', 'creditor_account',
            'creditor_agent', 'instructed_amount', 'currency',
            'purpose_code', 'requested_execution_date',
            'remittance_information_structured', 'remittance_information_unstructured'
        ]
        widgets = {
            'debtor': forms.Select(attrs={'class': 'form-control'}),
            'debtor_account': forms.Select(attrs={'class': 'form-control'}),
            'creditor': forms.Select(attrs={'class': 'form-control'}),
            'creditor_account': forms.Select(attrs={'class': 'form-control'}),
            'creditor_agent': forms.Select(attrs={'class': 'form-control'}),
            'instructed_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose_code': forms.TextInput(attrs={'class': 'form-control'}),
            'requested_execution_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': datetime.now(pytz.timezone('Europe/Berlin')).strftime('%Y-%m-%d')
            }),
            'remittance_information_structured': forms.TextInput(attrs={
                'maxlength': 60,
                'class': 'form-control',
                'rows': 1,
                'placeholder': 'Ingrese información estructurada (máx. 60 caracteres)'
            }),
            'remittance_information_unstructured': forms.TextInput(attrs={
                'maxlength': 60,
                'class': 'form-control',
                'rows': 1,
                'placeholder': 'Ingrese información no estructurada (máx. 60 caracteres)'
            }),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.payment_type_information:
            instance.payment_type_information = PaymentTypeInformation.objects.create(
                service_level_code=self.cleaned_data.get('payment_type_information_service_level', 'INST'),
                local_instrument_code=self.cleaned_data.get('payment_type_information_local_instrument'),
                category_purpose_code=self.cleaned_data.get('payment_type_information_category_purpose')
            )
        if commit:
            instance.save()
        return instance


class SendTransferForm(forms.Form):
    instant_transfer = forms.BooleanField(
        required=False,
        label="¿Transferencia Instantánea?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    obtain_token = forms.BooleanField(
        required=False,
        label='Obtener nuevo TOKEN',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    manual_token = forms.CharField(
        required=False,
        label='TOKEN manual',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Introduce TOKEN manual si aplica'})
    )
    obtain_otp = forms.BooleanField(
        required=False,
        label='Obtener nuevo OTP',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    manual_otp = forms.CharField(
        required=False,
        label='OTP manual',
        min_length=6,
        max_length=8,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Introduce OTP manual de 6 a 8 caracteres'})
    )

    def clean(self):
        cleaned_data = super().clean()
        obtain_token = cleaned_data.get('obtain_token')
        manual_token = cleaned_data.get('manual_token')
        obtain_otp = cleaned_data.get('obtain_otp')
        manual_otp = cleaned_data.get('manual_otp')

        if not obtain_token and not manual_token:
            raise forms.ValidationError('Debes seleccionar obtener TOKEN o proporcionar uno manualmente.')

        if not obtain_otp and not manual_otp:
            raise forms.ValidationError('Debes seleccionar obtener OTP o proporcionar uno manualmente.')

        return cleaned_data
