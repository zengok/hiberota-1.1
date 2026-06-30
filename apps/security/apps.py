from __future__ import annotations

from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.security"

    def ready(self) -> None:
        from django.contrib import admin

        from apps.security.forms import SecureAdminAuthenticationForm

        admin.site.login_form = SecureAdminAuthenticationForm
