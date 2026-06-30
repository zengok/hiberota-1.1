from __future__ import annotations

from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError

from apps.security.admin_auth import (
    GENERIC_ADMIN_LOGIN_ERROR,
    admin_login_is_locked,
    record_failed_admin_login,
    reset_admin_login_attempts,
    verify_admin_totp,
)


class SecureAdminAuthenticationForm(AdminAuthenticationForm):
    otp_token = forms.CharField(
        label="Authenticator code",
        max_length=6,
        min_length=6,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code", "inputmode": "numeric"}),
    )

    def clean(self) -> dict[str, str]:
        username = self.cleaned_data.get("username", "")
        if self.request and admin_login_is_locked(self.request, username):
            raise ValidationError(GENERIC_ADMIN_LOGIN_ERROR, code="admin_login_locked")

        try:
            cleaned_data = super().clean()
        except ValidationError as exc:
            if self.request:
                record_failed_admin_login(self.request, username)
            raise ValidationError(GENERIC_ADMIN_LOGIN_ERROR, code="admin_login_failed") from exc

        otp_token = cleaned_data.get("otp_token", "")
        if self.user_cache is None or not verify_admin_totp(self.user_cache, otp_token):
            if self.request:
                record_failed_admin_login(self.request, username)
            raise ValidationError(GENERIC_ADMIN_LOGIN_ERROR, code="admin_totp_failed")

        if self.request:
            reset_admin_login_attempts(self.request, username)
        return cleaned_data
