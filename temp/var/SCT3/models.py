from django.db import models

class Debtor(models.Model):
    name = models.CharField(max_length=140)
    country = models.CharField(max_length=2)
    street_and_house_number = models.CharField(max_length=70, blank=True, null=True)
    zip_code_and_city = models.CharField(max_length=70, blank=True, null=True)

    def __str__(self):
        return self.name

class Creditor(models.Model):
    name = models.CharField(max_length=70)
    country = models.CharField(max_length=2)
    street_and_house_number = models.CharField(max_length=70, blank=True, null=True)
    zip_code_and_city = models.CharField(max_length=70, blank=True, null=True)

    def __str__(self):
        return self.name

class SepaCreditTransfer(models.Model):
    payment_id = models.CharField(max_length=100, unique=True)
    transaction_status = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    debtor = models.ForeignKey(Debtor, on_delete=models.CASCADE)
    creditor = models.ForeignKey(Creditor, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.payment_id} - {self.transaction_status}"
