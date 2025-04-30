from django.db import models
from api.gpt4.utils import generate_unique_code

class Debtor(models.Model):
    name = models.CharField(max_length=70, unique=True, blank=False)
    customer_id = models.CharField(max_length=35, unique=True, blank=False)
    postal_address_country = models.CharField(max_length=2, blank=False)
    postal_address_street = models.CharField(max_length=70, blank=False, unique=True)
    postal_address_city = models.CharField(max_length=70, blank=False)

    def __str__(self):
        return self.name

class DebtorAccount(models.Model):
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE, blank=False)
    iban = models.CharField(max_length=34, unique=True, blank=False)
    currency = models.CharField(max_length=3, blank=False)

    def __str__(self):
        return f"{self.debtor.name} - {self.iban}"

class Creditor(models.Model):
    name = models.CharField(max_length=70, unique=True, blank=False)
    postal_address_country = models.CharField(max_length=2, blank=False)
    postal_address_street = models.CharField(max_length=70, blank=False, unique=True)
    postal_address_city = models.CharField(max_length=70, blank=False)

    def __str__(self):
        return self.name

class CreditorAccount(models.Model):
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)
    iban = models.CharField(max_length=34, unique=True, blank=False)
    currency = models.CharField(max_length=3, blank=False)

    def __str__(self):
        return f"{self.creditor.name} - {self.iban}"

class CreditorAgent(models.Model):
    bic = models.CharField(max_length=11, blank=False, unique=True)
    financial_institution_id = models.CharField(max_length=35, blank=False, unique=True)
    other_information = models.CharField(max_length=70, blank=False, unique=True)

    def __str__(self):
        return self.bic or self.financial_institution_id or "Agent"

class PaymentIdentification(models.Model):
    end_to_end_id = models.CharField(max_length=35)
    instruction_id = models.CharField(max_length=35)

    def __str__(self):
        return self.end_to_end_id


SERVICE_LEVEL_CHOICES = [
    ('SEPA', 'SEPA estándar'),
    ('URGENT', 'Urgente'),
    ('INST', 'SEPA Instantánea'),
]

LOCAL_INSTRUMENT_CHOICES = [
    ('INST', 'SEPA Instantáneo'),
    ('CORE', 'Adeudo Directo SEPA CORE'),
    ('B2B', 'Adeudo Directo SEPA B2B'),
    ('URGP', 'Pago Urgente Europeo'),
]

CATEGORY_PURPOSE_CHOICES = [
    ('SALA', 'Salario'),
    ('TAXS', 'Impuestos'),
    ('SUPP', 'Proveedores'),
    ('CORT', 'Pago de préstamo'),
    ('GDSV', 'Bienes y servicios'),
]

class PaymentTypeInformation(models.Model):
    service_level_code = models.CharField(
        max_length=10,
        choices=SERVICE_LEVEL_CHOICES,
        default='INST',
    )
    local_instrument_code = models.CharField(
        max_length=35,
        choices=LOCAL_INSTRUMENT_CHOICES,
        default='INST',
        blank=True,
        null=True
    )
    category_purpose_code = models.CharField(
        max_length=35,
        choices=CATEGORY_PURPOSE_CHOICES,
        default='GDSV',
        blank=True,
        null=True
    )
    
class Transfer(models.Model):
    payment_id = models.CharField(max_length=35, unique=True, default=generate_unique_code)
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE)
    debtor_account = models.ForeignKey(DebtorAccount, on_delete=models.CASCADE)
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)
    creditor_account = models.ForeignKey(CreditorAccount, on_delete=models.CASCADE)
    creditor_agent = models.ForeignKey(CreditorAgent, on_delete=models.CASCADE)
    instructed_amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    purpose_code = models.CharField(max_length=4, default='GDSV')
    requested_execution_date = models.DateField()
    remittance_information_structured = models.CharField(max_length=10, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)
    status = models.CharField(max_length=10, default='CREA', choices=[
        ('RJCT', 'Rechazada'),
        ('RCVD', 'Recibida'),
        ('ACCP', 'Aceptada'),
        ('ACTC', 'Aceptada técnicamente'),
        ('ACSP', 'En proceso'),
        ('ACSC', 'Ejecutada con éxito'),
        ('ACWC', 'Con advertencia'),
        ('ACWP', 'Pendiente de aprobación'),
        ('ACCC', 'Concluida'),
        ('CANC', 'Cancelada'),
        ('PDNG', 'Pendiente'),
        ('CREA', 'Creada'),

    ])
    payment_identification = models.ForeignKey(PaymentIdentification, on_delete=models.CASCADE)
    payment_type_information = models.ForeignKey(PaymentTypeInformation, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    _instant_transfer_flag = False  # Propiedad temporal, no se guarda en la DB
    def set_instant_transfer(self, value: bool):
        self._instant_transfer_flag = bool(value)
        
    def to_schema_data(self, instant_transfer=False):
        instant_transfer = self._instant_transfer_flag
        return {
            "purposeCode": self.purpose_code or "GDSV",
            "requestedExecutionDate": self.requested_execution_date.strftime('%Y-%m-%d'),
            "debtor": {
                "debtorName": self.debtor.name,
                "debtorPostalAddress": {
                    "country": self.debtor.postal_address_country,
                    "addressLine": {
                        "streetAndHouseNumber": self.debtor.postal_address_street,
                        "zipCodeAndCity": self.debtor.postal_address_city,
                    }
                }
            },
            "debtorAccount": {
                "iban": self.debtor_account.iban,
                "currency": self.debtor_account.currency,
            },
            "instructedAmount": {
                "amount": float(self.instructed_amount),
                "currency": self.currency,
            },
            "creditorAgent": {
                "financialInstitutionId": self.creditor_agent.financial_institution_id or "",
            },
            "creditor": {
                "creditorName": self.creditor.name,
                "creditorPostalAddress": {
                    "country": self.creditor.postal_address_country,
                    "addressLine": {
                        "streetAndHouseNumber": self.creditor.postal_address_street,
                        "zipCodeAndCity": self.creditor.postal_address_city,
                    }
                }
            },
            "creditorAccount": {
                "iban": self.creditor_account.iban,
                "currency": self.creditor_account.currency,
            },
            "remittanceInformationUnstructured": self.remittance_information_unstructured or "Pago de servicios",
        }

    def save(self, *args, **kwargs):
        # Asignar automáticamente servicio INST si no se especifica
        if not self.payment_type_information:
            pti = PaymentTypeInformation.objects.create(service_level_code='INST')
            self.payment_type_information = pti
        super().save(*args, **kwargs)

    def get_status_color(self):
        return {
            'PDNG': 'warning',
            'ACSC': 'success',
            'RJCT': 'danger',
            'CANC': 'secondary'
        }.get(self.status, 'dark')
        
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.payment_id

class LogTransferencia(models.Model):
    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE)
    log_file = models.FileField(upload_to='logs/transferencias/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log de {self.transfer.payment_id}"
