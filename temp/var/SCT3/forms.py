from django import forms

class SepaFilterForm(forms.Form):
    transaction_status = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('ACCP', 'Aceptado'),
            ('RJCT', 'Rechazado'),
            ('PDNG', 'Pendiente'),
        ],
        required=False,
        label="Estado de Transacción"
    )
