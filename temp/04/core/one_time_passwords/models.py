from django.db import models

class ChallengeMethodType(models.TextChoices):
    MTAN = 'MTAN'
    PHOTOTAN = 'PHOTOTAN'
    PUSHTAN = 'PUSHTAN'

class ChallengeMethodMetadata(models.Model):
    mobilePhoneNumber = models.CharField(max_length=20)
    activeDevicesCount = models.IntegerField()

class ChallengeMethodItem(models.Model):
    method = models.CharField(max_length=50, choices=ChallengeMethodType.choices)
    status = models.CharField(max_length=50)
    metadata = models.ForeignKey(ChallengeMethodMetadata, on_delete=models.CASCADE)

class ChallengeRequest(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    method = models.CharField(max_length=50, choices=ChallengeMethodType.choices)
    challenge = models.JSONField()

class ChallengeResponse(models.Model):
    challengeResponse = models.CharField(max_length=255)

class ChallengeResult(models.Model):
    otp = models.CharField(max_length=255)

class OrderLimit(models.Model):
    limitPrice = models.FloatField()
    stopPrice = models.FloatField()

class OrderAddOns(models.Model):
    expiryDate = models.DateField()
    restriction = models.CharField(max_length=50)

class ChallengeRequestDataTransferPartnerLegiData(models.Model):
    type = models.CharField(max_length=255)

class ChallengeRequestDataSecuritiesOrderEntry(models.Model):
    type = models.CharField(max_length=255)
    securityAccountId = models.CharField(max_length=12)
    securityId = models.CharField(max_length=6)
    quantity = models.FloatField()
    activityType = models.CharField(max_length=50)
    orderLimit = models.ForeignKey(OrderLimit, on_delete=models.CASCADE)
    addOns = models.ForeignKey(OrderAddOns, on_delete=models.CASCADE)

class ChallengeRequestDataSecuritiesOrderModify(models.Model):
    type = models.CharField(max_length=255)
    orderId = models.CharField(max_length=255)
    securityAccountId = models.CharField(max_length=12)
    orderLimit = models.ForeignKey(OrderLimit, on_delete=models.CASCADE)
    addOns = models.ForeignKey(OrderAddOns, on_delete=models.CASCADE)

class ChallengeRequestDataSecuritiesOrderDelete(models.Model):
    type = models.CharField(max_length=255)
    orderId = models.CharField(max_length=255)
    securityAccountId = models.CharField(max_length=12)

class ChallengeRequestDataInstantSepaCreditTransfers(models.Model):
    type = models.CharField(max_length=255)
    targetIban = models.CharField(max_length=34)
    amountCurrency = models.CharField(max_length=3)
    amountValue = models.FloatField()
