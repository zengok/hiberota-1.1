from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from apps.security.models import AdminTOTPDevice
from apps.security.totp import build_totp_uri, generate_totp_secret


class Command(BaseCommand):
    help = "Provision or rotate a TOTP device for a staff admin user."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("username")
        parser.add_argument("--issuer", default="HibeRota")
        parser.add_argument("--rotate", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        username = str(options["username"])
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=username)
        except user_model.DoesNotExist as exc:
            raise CommandError("Staff admin user not found.") from exc

        if not user.is_staff:
            raise CommandError("TOTP can only be provisioned for staff admin users.")

        existing = AdminTOTPDevice.objects.filter(user=user).first()
        if existing and not options["rotate"]:
            raise CommandError("TOTP device already exists. Use --rotate to replace it.")

        secret = generate_totp_secret()
        device, _ = AdminTOTPDevice.objects.update_or_create(
            user=user,
            defaults={
                "name": "Authenticator app",
                "secret_key": secret,
                "confirmed_at": timezone.now(),
                "last_used_at": None,
                "last_counter": None,
                "is_active": True,
            },
        )
        otpauth_uri = build_totp_uri(issuer=str(options["issuer"]), account_name=user.get_username(), secret=secret)

        self.stdout.write(self.style.SUCCESS(f"TOTP device ready for {device.user.get_username()}"))
        self.stdout.write("Add this otpauth URI to the admin's authenticator app over a secure channel:")
        self.stdout.write(otpauth_uri)
