from django.db import models

class CurrencyCode(models.Model):
    currency_code = models.CharField(max_length=3)  # ISO 4217
    def __str__(self):
        return super().__str__(self.currency_code)

class ErrorResponse(models.Model):
    message_error_id = models.AutoField(primary_key=True)
    code = models.IntegerField()
    message = models.TextField()
    def __str__(self):
        return super().__str__(self.message_error_id)

class IBAN(models.Model):
    iban = models.CharField(max_length=34)
    def __str__(self):
        return super().__str__(self.iban)
    
class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    code = models.IntegerField()
    message = models.TextField()
    def __str__(self):
        return super().__str__(self.message_id)
    
class TransactionStatus(models.Model):
    enum = [
        ('ACCP', 'ACCP'), #ACCP - AcceptedCustomerProfile. Preceding check of technical validation was successful. Customer profile check was also successful.
        ('RJCT', 'RJCT'), #RJCT - Rejected. Payment initiation or individual transaction included in the payment initiation has been rejected.
        ('CARJ', 'CARJ'), #CARJ - Rejected. Payment initiation or individual transaction included in the payment initiation has been rejected because the client rejected the PUSHTAN request.
        ('PYLE', 'PYLE'), #PYLE - Rejected. Payment initiation or individual transaction included in the payment initiation has been rejected because payment limit was reached.
        ('PDNG', 'PDNG'), #PDNG - Pending. Payment initiation or individual transaction included in the payment initiation is pending. Further checks and status update will be performed.
        ('ACAT', 'ACAT'), #ACAT - Pending. Waiting for customer authorization. Further checks and status update will be performed.
    ]
    transaction_status = models.CharField(max_length=4, choices=enum, default='PDNG')

    def __str__(self):
        return super().__str__(self.transaction_status)

class ReachabilityResponse(models.Model):
    is_instant_payment_reachable = models.BooleanField()

class StatusResponse(models.Model):
    category = models.CharField(max_length=20, blank=False)
    code = models.ForeignKey(TransactionStatus, on_delete=models.CASCADE)
    text = models.CharField(max_length=50)

class AccountReference(models.Model):
    currency_code = models.ForeignKey(CurrencyCode, on_delete=models.CASCADE)
    iban = models.ForeignKey(IBAN, on_delete=models.CASCADE)

class Amount(models.Model):
    currency_code = models.ForeignKey(CurrencyCode, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)

class Address(models.Model):
    building_number = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=2, blank=False)  # ISO 3166-1 alpha-2
    postal_code = models.CharField(max_length=20, blank=True)
    street = models.CharField(max_length=70, blank=True)

class PaymentRequest(models.Model):
    payment_request_id = models.AutoField(primary_key=True)
    creditor_account = models.ForeignKey(AccountReference, on_delete=models.CASCADE, related_name='creditor_account')
    creditor_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='creditor_address', blank=True, null=True)
    creditor_agent = models.CharField(max_length=11, blank=True)
    creditor_name = models.CharField(max_length=70)
    debtor_account = models.ForeignKey(AccountReference, on_delete=models.CASCADE, related_name='debtor_account')
    end_to_end_identification = models.CharField(max_length=35, blank=False, unique=True)
    instructed_amount = models.ForeignKey(Amount, on_delete=models.CASCADE)
    remittance_information_unstructured = models.CharField(max_length=140, blank=True)
    def __str__(self):
        return super().__str__(self.payment_request_id)

class PaymentResponse(models.Model):
    payment_id = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE)
    transaction_status = models.ForeignKey(TransactionStatus, on_delete=models.CASCADE)


