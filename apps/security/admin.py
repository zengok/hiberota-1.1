from __future__ import annotations

from django.contrib import admin

from apps.security.models import AdminTOTPDevice


@admin.register(AdminTOTPDevice)
class AdminTOTPDeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "is_active", "confirmed_at", "last_used_at")
    list_filter = ("is_active", "confirmed_at")
    search_fields = ("user__username", "user__email", "name")
    readonly_fields = ("created_at", "updated_at", "last_used_at", "last_counter", "masked_secret_key")
    fields = (
        "user",
        "name",
        "masked_secret_key",
        "confirmed_at",
        "last_used_at",
        "last_counter",
        "is_active",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Secret key")
    def masked_secret_key(self, obj: AdminTOTPDevice) -> str:
        if not obj.secret_key:
            return ""
        return f"{obj.secret_key[:4]}...{obj.secret_key[-4:]}"
