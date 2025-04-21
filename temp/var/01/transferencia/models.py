from django.db import models
from django.contrib.auth.models import User

class Transferencia(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20)
    origin_iban = models.CharField(max_length=34)
    origin_bic = models.CharField(max_length=11)
    origin_account_number = models.CharField(max_length=34)  # Nuevo campo
    origin_account_holder_name = models.CharField(max_length=100)  # Nuevo campo
    currency_code = models.CharField(max_length=3)
    counter_party_bank_name = models.CharField(max_length=100)
    counter_party_account_number = models.CharField(max_length=34)
    counter_party_name = models.CharField(max_length=100)
    counter_party_bic = models.CharField(max_length=11)
    payment_reference = models.CharField(max_length=50)
    swift_transaction_id = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Nuevo campo
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transferencia {self.payment_reference}"