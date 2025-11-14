# salla/models.py

from django.db import models
from django.utils import timezone


class WebhookEvent(models.Model):
    event_id = models.CharField(max_length=150, unique=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    signature_valid = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} ({self.event_id})"


class SallaOrder(models.Model):
    order_id = models.BigIntegerField(unique=True)
    full_payload = models.JSONField()
    standard_status = models.CharField(max_length=100)
    custom_status = models.CharField(max_length=150, blank=True, default="")
    last_event = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)


class IntegrationToken(models.Model):
    provider = models.CharField(max_length=50, default="SALLA")
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # from Easy Mode "expires"
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return self.expires_at and timezone.now() >= self.expires_at
