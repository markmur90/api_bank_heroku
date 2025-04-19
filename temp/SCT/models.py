from django.db import models
from django.core.validators import RegexValidator

class TransactionStatus(models.TextChoices):
    RJCT = "RJCT", "Rejected"
    RCVD = "RCVD", "Received"
    ACCP = "ACCP", "Accepted"
    ACTC = "ACTC", "Accepted Technical Validation"
    ACSP = "ACSP", "Accepted Settlement in Process"
    ACSC = "ACSC", "Accepted Settlement Completed"
    ACWC = "ACWC", "Accepted with Change"
    ACWP = "ACWP", "Accepted with Pending"
    ACCC = "ACCC", "Accepted Credit Check"
    CANC = "CANC", "Cancelled"
    PDNG = "PDNG", "Pending"

class Action(models.TextChoices):
    CREATE = "CREATE", "Create"
    CANCEL = "CANCEL", "Cancel"

# ISO 20022-related models
class CategoryPurpose(models.Model):
    code = models.CharField(max_length=4, help_text="Category purpose code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)

class ServiceLevel(models.Model):
    code = models.CharField(max_length=4, help_text="Service level code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)

class LocalInstrument(models.Model):
    code = models.CharField(max_length=4, help_text="Local instrument code as per ISO 20022.")
    description = models.CharField(max_length=140, blank=True, null=True)

# Address-related models
class AddressLine(models.Model):
    street_and_house_number = models.CharField(max_length=70, blank=True, null=True)
    zip_code_and_city = models.CharField(max_length=70, blank=True, null=True)

class Address(models.Model):
    country = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 country code")
    address_line = models.OneToOneField(AddressLine, on_delete=models.CASCADE, null=True, blank=True)

# Debtor-related models
class DebtorName(models.Model):
    name = models.CharField(max_length=140)

class Debtor(models.Model):
    name = models.CharField(max_length=140)
    postal_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)

class DebtorAccount(models.Model):
    iban = models.CharField(max_length=34)  # IBAN max length is 34
    currency = models.CharField(max_length=3, help_text="ISO 4217 Alpha 3 currency code")

# Creditor-related models
class CreditorName(models.Model):
    name = models.CharField(max_length=70)

class Creditor(models.Model):
    name = models.CharField(max_length=70)
    postal_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)

class CreditorAccount(models.Model):
    iban = models.CharField(max_length=34)
    currency = models.CharField(max_length=3)

class CreditorAgent(models.Model):
    financial_institution_id = models.CharField(max_length=255)

# Payment-related models
class PaymentIdentification(models.Model):
    end_to_end_id = models.CharField(max_length=35, blank=True, null=True, validators=[RegexValidator(regex=r'^[a-zA-Z0-9.-]{1,35}$', message="Unique identification assigned by the initiating party to unambiguously identify the transaction")])
    instruction_id = models.CharField(max_length=35, blank=True, null=True, validators=[RegexValidator(regex=r'^[a-zA-Z0-9.-]{1,35}$', message="Instruction ID must match the pattern [a-zA-Z0-9.-]{1,35}")])

class InstructedAmount(models.Model):
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3)

class SepaCreditTransferRequest(models.Model):
    purpose_code = models.CharField(max_length=4, blank=True, null=True)
    requested_execution_date = models.DateField(blank=True, null=True)  # Formato: yyyy-MM-dd (manejar en formularios o serializadores)
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE)
    debtor_account = models.ForeignKey(DebtorAccount, on_delete=models.CASCADE)
    payment_identification = models.ForeignKey(PaymentIdentification, on_delete=models.SET_NULL, null=True, blank=True)
    instructed_amount = models.ForeignKey(InstructedAmount, on_delete=models.CASCADE)
    creditor_agent = models.ForeignKey(CreditorAgent, on_delete=models.CASCADE)
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)
    creditor_account = models.ForeignKey(CreditorAccount, on_delete=models.CASCADE)
    remittance_information_structured = models.CharField(max_length=140, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)

class SepaCreditTransferUpdateScaRequest(models.Model):
    action = models.CharField(max_length=10, choices=Action.choices, help_text="Defines the action for retry second factor. CREATE is for updating the second factor for create Sepa Credit Transfer and CANCEL is for cancel.")
    auth_id = models.UUIDField()

class SepaCreditTransferResponse(models.Model):
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices)
    payment_id = models.UUIDField()
    auth_id = models.UUIDField()

class SepaCreditTransferDetailsResponse(models.Model):
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices)
    payment_id = models.UUIDField()
    purpose_code = models.CharField(max_length=4, blank=True, null=True)
    requested_execution_date = models.DateField(blank=True, null=True)  # Formato: yyyy-MM-dd (manejar en formularios o serializadores)
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE)
    debtor_account = models.ForeignKey(DebtorAccount, on_delete=models.CASCADE)
    creditor_agent = models.ForeignKey(CreditorAgent, on_delete=models.CASCADE)
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)
    creditor_account = models.ForeignKey(CreditorAccount, on_delete=models.CASCADE)
    payment_identification = models.ForeignKey(PaymentIdentification, on_delete=models.SET_NULL, null=True, blank=True)
    instructed_amount = models.ForeignKey(InstructedAmount, on_delete=models.CASCADE)
    remittance_information_structured = models.CharField(max_length=140, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)

# Error and status models
class ErrorResponse(models.Model):
    code = models.IntegerField()
    message = models.CharField(max_length=140, blank=True, null=True)
    message_id = models.CharField(max_length=255, blank=True, null=True)



