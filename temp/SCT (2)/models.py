from django.db import models
from .choices import TRANSACTION_STATUS_CHOICES, ACTION_CHOICES

class Address(models.Model):
    country = models.CharField(max_length=2)
    street_and_house_number = models.CharField(max_length=70, blank=True, null=True)
    zip_code_and_city = models.CharField(max_length=70, blank=True, null=True)

class Debtor(models.Model):
    name = models.CharField(max_length=140)
    postal_address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True)

class Creditor(models.Model):
    name = models.CharField(max_length=70)
    postal_address = models.OneToOneField(Address, on_delete=models.CASCADE, null=True, blank=True)

class Account(models.Model):
    iban = models.CharField(max_length=34)
    currency = models.CharField(max_length=3)

class InstructedAmount(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)

class SepaCreditTransfer(models.Model):
    debtor = models.OneToOneField(Debtor, on_delete=models.CASCADE)
    debtor_account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="debtor_account")
    creditor = models.OneToOneField(Creditor, on_delete=models.CASCADE)
    creditor_account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="creditor_account")
    instructed_amount = models.OneToOneField(InstructedAmount, on_delete=models.CASCADE)
    transaction_status = models.CharField(max_length=4, choices=TRANSACTION_STATUS_CHOICES)
    payment_id = models.UUIDField(unique=True)
    auth_id = models.UUIDField()
    purpose_code = models.CharField(max_length=4, blank=True, null=True)
    requested_execution_date = models.DateField(blank=True, null=True)
    remittance_information_structured = models.CharField(max_length=140, blank=True, null=True)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, null=True)
