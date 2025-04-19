from django.utils import timezone
from django.db import models

class CurrencyCode(models.Model):
    currency_code = models.CharField(max_length=3)  # ISO 4217
    def __str__(self):
        return self.currency_code

class ErrorResponse(models.Model):
    code = models.IntegerField()
    message = models.TextField()
    messageId = models.AutoField(primary_key=True) # dbAPI internal message-id (unique identifier) that allow reference to each of your API calls.
    def __str__(self):
        return str(self.messageId)

class IBAN(models.Model):
    iban = models.CharField(max_length=34)
    def __str__(self):
        return self.iban
    
class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    code = models.IntegerField()
    message = models.TextField()
    def __str__(self):
        return str(self.message_id)
    
class TransactionStatus(models.Model):
    transaction_status = models.CharField(max_length=4, default='PDNG')
    description = models.CharField(max_length=250, blank=True)
    def __str__(self):
        return f'{self.transaction_status} - {self.description}'

class ReachabilityResponse(models.Model):
    is_instant_payment_reachable = models.BooleanField()

class StatusResponse(models.Model):
    category = models.CharField(max_length=20, blank=False)
    code = models.ForeignKey(TransactionStatus, on_delete=models.CASCADE)
    text = models.CharField(max_length=50)
    def __str__(self):
        return f'{self.code} - {self.text}'

class AccountReference(models.Model):
    currency_code = models.ForeignKey(CurrencyCode, on_delete=models.CASCADE)
    iban = models.ForeignKey(IBAN, on_delete=models.CASCADE)
    swift = models.CharField(max_length=11, blank=False)
    def __str__(self):
        return f'{self.iban} - {self.currency_code}'

class Amount(models.Model):
    currency_code = models.ForeignKey(CurrencyCode, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    def __str__(self):
        return f'{self.currency_code} - {self.amount}'

class Address(models.Model):
    building_number = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=2, blank=False)  # ISO 3166-1 alpha-2
    postal_code = models.CharField(max_length=20, blank=True)
    street = models.CharField(max_length=70, blank=True)
    def __str__(self):
        return f'{self.building_number} - {self.city} - {self.country} - {self.postal_code} - {self.street}'
    
class PaymentRequest(models.Model):
    creditor_name = models.CharField(max_length=70, name='creditor_name')
    creditor_account = models.ForeignKey(AccountReference, on_delete=models.CASCADE, related_name='creditor_account')
    creditor_bank = models.CharField(max_length=70, name='creditor_bank')
    creditor_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='creditor_address', blank=True, null=True, name='creditor_address')
    creditor_agent = models.CharField(max_length=11,  name='creditor_agent')

    debtor_name = models.CharField(max_length=70, name='debtor_name')    
    debtor_account = models.ForeignKey(AccountReference, on_delete=models.CASCADE, related_name='debtor_account')
    debtor_bank = models.CharField(max_length=70, name='debtor_bank')
    debtor_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='debtor_address', blank=True, null=True, name='debtor_address')
    debtor_agent = models.CharField(max_length=11,  name='debtor_agent')

    end_to_end_identification = models.CharField(max_length=35, blank=False, unique=True, name='end_to_end_identification')
    instructed_amount = models.ForeignKey(Amount, on_delete=models.CASCADE)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True, name='remittance_information_unstructured')
    payment_date = models.DateTimeField(default=timezone.now, name='payment_date')

    def __str__(self):
        return str(self.id)
 
class PaymentResponse(models.Model):
    payment_id = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE)
    transaction_status = models.ForeignKey(TransactionStatus, on_delete=models.CASCADE)


