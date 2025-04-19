from django.db import models

class TransferenciaSWIFT(models.Model):
    # Datos del banco emisor (Deutsche Bank)
    banco_origen = models.CharField(max_length=100, default="Deutsche Bank AG")
    codigo_swift_origen = models.CharField(max_length=20, default="DEUTDEFFXXX")
    numero_cuenta_origen = models.CharField(max_length=50, default="010581700")
    nombre_origen = models.CharField(max_length=50, default="EQUITY & CAPITAL VENTURES LIMITED")
     
    # Datos del banco receptor
    banco_destino = models.CharField(max_length=100)
    codigo_swift_destino = models.CharField(max_length=20)
    numero_cuenta_destino = models.CharField(max_length=50)
    nombre_beneficiario = models.CharField(max_length=100)
    
    # Detalles de la transacción
    moneda = models.CharField(max_length=10, default="EUR")
    monto = models.DecimalField(max_digits=30, decimal_places=2)
    referencia = models.CharField(max_length=50, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default="Pendiente")  # Pendiente, Completada, Fallida

    def __str__(self):
        return f"Transferencia {self.referencia} - {self.monto} {self.moneda} a {self.banco_destino}"