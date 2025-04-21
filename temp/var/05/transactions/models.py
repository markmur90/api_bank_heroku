from django.db import models
from django.contrib.auth.models import User

class Transferencia(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    origin_iban = models.CharField(max_length=34)
    origin_bic = models.CharField(max_length=11)
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    currency_code = models.CharField(max_length=3, default="EUR")
    counter_party_bank_name = models.CharField(max_length=100)
    counter_party_account_number = models.CharField(max_length=34)
    counter_party_name = models.CharField(max_length=100)
    counter_party_bic = models.CharField(max_length=11)
    payment_reference = models.CharField(maxlength=50)
    estado = models.CharField(max_length=20, choices=[('pendiente', 'Pendiente'), ('completado', 'Completado')])
    fecha = models.DateTimeField(auto_now_add=True)
