from django.db import models

class CashAccountTransaction(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    origin_iban = models.CharField(max_length=34)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    counter_party_name = models.CharField(max_length=255, blank=True, null=True)
    counter_party_iban = models.CharField(max_length=34, blank=True, null=True)
    counter_party_bic = models.CharField(max_length=11, blank=True, null=True)
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    booking_date = models.DateField()
    currency_code = models.CharField(max_length=3)
    transaction_code = models.CharField(max_length=255, blank=True, null=True)
    external_bank_transaction_domain_code = models.CharField(max_length=255, blank=True, null=True)
    external_bank_transaction_family_code = models.CharField(max_length=4, blank=True, null=True)
    external_bank_transaction_sub_family_code = models.CharField(max_length=255, blank=True, null=True)
    mandate_reference = models.CharField(max_length=35, blank=True, null=True)
    creditor_id = models.CharField(max_length=35, blank=True, null=True)
    e2e_reference = models.CharField(max_length=255, blank=True, null=True)
    payment_identification = models.CharField(max_length=255, blank=True, null=True)
    value_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.origin_iban} - {self.amount} {self.currency_code}"