from django.db import models
from django.utils import timezone


class FunnerLifeService(models.Model):
    service_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    price_gold = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True) 
    price_silver = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_pro = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20)
    last_synced_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.category})"
