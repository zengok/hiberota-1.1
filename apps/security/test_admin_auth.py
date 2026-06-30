from __future__ import annotations

import time

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.utils import timezone

from apps.security.admin_auth import admin_login_is_locked, record_failed_admin_login
from apps.security.forms import SecureAdminAuthenticationForm
from apps.security.models import AdminTOTPDevice
from apps.security.totp import build_totp_uri, generate_totp_secret, totp_token

TEST_ADMIN_CREDENTIAL = "correct" + "-password"
TEST_PUBLIC_CREDENTIAL = "public" + "-credential"
TEST_TOTP_SEED = "JBSWY3DPEHPK3PXP"
BLANK_CODE = ""


class AdminTOTPTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.factory = RequestFactory(REMOTE_ADDR="203.0.113.20")
        self.user = self._create_staff_user()
        self.totp_seed = TEST_TOTP_SEED
        self.device = AdminTOTPDevice.objects.create(
            user=self.user,
            secret_key=self.totp_seed,
            confirmed_at=timezone.now(),
            is_active=True,
        )

    def test_default_admin_site_uses_secure_login_form(self) -> None:
        self.assertIs(admin.site.login_form, SecureAdminAuthenticationForm)

    def test_totp_token_is_required_for_staff_admin_login(self) -> None:
        request = self.factory.post("/admin/login/")
        counter = int(time.time()) // 30
        token = totp_token(self.totp_seed, counter=counter)
        form = SecureAdminAuthenticationForm(
            request,
            data={
                "username": "editor",
                "password": TEST_ADMIN_CREDENTIAL,
                "otp_token": token,
            },
        )

        with override_settings(ADMIN_TOTP_REQUIRED=True):
            self.assertTrue(form.is_valid())

        self.device.refresh_from_db()
        self.assertEqual(self.device.last_counter, counter)
        self.assertIsNotNone(self.device.last_used_at)

    def test_replayed_totp_token_is_rejected(self) -> None:
        counter = int(time.time()) // 30
        self.device.last_counter = counter
        self.device.save(update_fields=["last_counter"])
        request = self.factory.post("/admin/login/")
        form = SecureAdminAuthenticationForm(
            request,
            data={
                "username": "editor",
                "password": TEST_ADMIN_CREDENTIAL,
                "otp_token": totp_token(self.totp_seed, counter=counter),
            },
        )

        with override_settings(ADMIN_TOTP_REQUIRED=True):
            self.assertFalse(form.is_valid())

    def test_admin_login_locks_after_configured_failures(self) -> None:
        request = self.factory.post("/admin/login/")

        with override_settings(ADMIN_LOGIN_RATE_LIMIT_ATTEMPTS=2, ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS=300):
            record_failed_admin_login(request, "editor")
            self.assertFalse(admin_login_is_locked(request, "editor"))
            record_failed_admin_login(request, "editor")
            self.assertTrue(admin_login_is_locked(request, "editor"))

    def test_totp_can_be_temporarily_disabled_for_emergency_recovery(self) -> None:
        request = self.factory.post("/admin/login/")
        form = SecureAdminAuthenticationForm(
            request,
            data={
                "username": "editor",
                "password": TEST_ADMIN_CREDENTIAL,
                "otp_token": BLANK_CODE,
            },
        )

        with override_settings(ADMIN_TOTP_REQUIRED=False):
            self.assertTrue(form.is_valid())

    def test_non_staff_user_cannot_be_provisioned(self) -> None:
        user_model = get_user_model()
        user_model.objects.create_user(username="public", password=TEST_PUBLIC_CREDENTIAL)

        with self.assertRaisesMessage(Exception, "TOTP can only be provisioned for staff admin users."):
            call_command("provision_admin_totp", "public")

    def _create_staff_user(self) -> User:
        user_model = get_user_model()
        return user_model.objects.create_user(
            username="editor",
            password=TEST_ADMIN_CREDENTIAL,
            is_staff=True,
        )


class TOTPUtilityTests(TestCase):
    def test_generated_secret_and_uri_are_authenticator_compatible(self) -> None:
        secret = generate_totp_secret()
        uri = build_totp_uri(issuer="HibeRota", account_name="editor", secret=secret)

        self.assertGreaterEqual(len(secret), 32)
        self.assertTrue(uri.startswith("otpauth://totp/HibeRota%3Aeditor"))
        self.assertIn(f"secret={secret}", uri)
        self.assertIn("issuer=HibeRota", uri)
