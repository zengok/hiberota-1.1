from __future__ import annotations

from django.conf import settings
from django.db import models


class AdminTOTPDevice(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_totp_device")
    name = models.CharField(max_length=80, default="Authenticator app")
    secret_key = models.CharField(max_length=64)
    confirmed_at = models.DateTimeField()
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_counter = models.BigIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin TOTP device"
        verbose_name_plural = "Admin TOTP devices"

    def __str__(self) -> str:
        return f"{self.user} - {self.name}"
