from __future__ import annotations

from django.contrib import admin
from django.test import SimpleTestCase

from apps.contact.admin import ContactMessageAdmin
from apps.contact.models import ContactMessage


class ContactAdminTests(SimpleTestCase):
    def test_contact_message_is_registered_as_admin_inbox(self) -> None:
        model_admin = admin.site._registry[ContactMessage]

        self.assertIsInstance(model_admin, ContactMessageAdmin)
        self.assertIn("status", model_admin.list_filter)
        self.assertIn("message", model_admin.readonly_fields)
