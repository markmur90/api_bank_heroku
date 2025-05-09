from django.db import models

class Debtor(models.Model):
    name = models.CharField(max_length=70, unique=True, blank=False, default='MIRYA TRADING CO LTD')
    customer_id = models.CharField(max_length=35, unique=True, blank=False, default='27CDBFRDE17BEH')
    postal_address_country = models.CharField(max_length=2, blank=False, default='DE')
    postal_address_street = models.CharField(max_length=70, blank=False, unique=True, default='TAUNUSANLAGE 12')
    postal_address_city = models.CharField(max_length=70, blank=False, unique=True, default='60325 FRANKFURT')
    mobile_phone_number = models.CharField(
        max_length=15, blank=True, null=True,
        help_text="Formato internacional, e.g. +4915123456789"
    )    

    def __str__(self):
        return self.name

class DebtorAccount(models.Model):
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE, blank=False)
    iban = models.CharField(max_length=34, unique=True, blank=False, default='DE86500700100925993805')
    currency = models.CharField(max_length=3, blank=False, default='EUR')

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
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE, related_name='creditoraccount_set')
    iban = models.CharField(max_length=34, unique=True, blank=False)
    currency = models.CharField(max_length=3, blank=False, default='EUR')

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

class ClientID(models.Model):
    codigo = models.CharField(max_length=6, primary_key=True)
    clientId = models.CharField(max_length=60, unique=True, blank=True, null=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.clientId}"

class Kid(models.Model):
    codigo = models.CharField(max_length=6, primary_key=True)
    kid = models.CharField(max_length=60, unique=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.kid}"

class Transfer(models.Model):
    payment_id = models.CharField(max_length=36, unique=True)
    client = models.ForeignKey(ClientID, on_delete=models.CASCADE, related_name='transfers', blank=True, null=True)
    kid = models.ForeignKey(Kid, on_delete=models.CASCADE, related_name='transfersKID', blank=True, null=True)
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE)
    debtor_account = models.ForeignKey(DebtorAccount, on_delete=models.CASCADE)
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)
    creditor_account = models.ForeignKey(CreditorAccount, on_delete=models.CASCADE)
    creditor_agent = models.ForeignKey(CreditorAgent, on_delete=models.CASCADE)
    instructed_amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    purpose_code = models.CharField(max_length=4, default='GDSV')
    requested_execution_date = models.DateField()
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)
    status = models.CharField(max_length=10, choices=[
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
    auth_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_schema_data(self):
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
            "paymentIdentification": {
                "instructionId": self.payment_identification.instruction_id,
                "endToEndId":     self.payment_identification.end_to_end_id
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
            "remittanceInformationUnstructured": {
                self.remittance_information_unstructured
            }
        }
            

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


    
    
COD_01 = '27CDBFRDE17BEH'
COD_02 = 'DEUT27CDBFRDE17BEH'
COD_03 = 'IMAD-20250427-001'
COD_04 = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
COD_05 = 'SE0IWHFHJFHB848R9E0R9FRUFBCJHW0W9FHF008E88W0457338ASKH64880'
COD_06 = 'H858hfhg0ht40588hhfjpfhhd9944940jf'
COD_07 = '090512DEUTDEFFXXX886479'
COD_08 = 'DE0005140008'
COD_09 = 'DE86500700100925993805'
COD_10 = '25993805'
COD_11 = '0925993805'
COD_12 = '0105528001187'