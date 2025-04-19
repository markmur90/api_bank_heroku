from django import forms
from core.payments.models import ErrorResponse, Message, TransactionStatus, StatusResponse

class ErrorResponseForm(forms.ModelForm):
    class Meta:
        model = ErrorResponse
        fields = ['code', 'message']
        widgets = {
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['code', 'message']
        widgets = {
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control'}),
        }

class TransactionStatusForm(forms.ModelForm):
    class Meta:
        model = TransactionStatus
        fields = ['transaction_status', 'description']
        widgets = {
            'transaction_status': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }

class StatusResponseForm(forms.ModelForm):
    class Meta:
        model = StatusResponse
        fields = ['category', 'code', 'text']
        widgets = {
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.Select(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control'}),
        }
