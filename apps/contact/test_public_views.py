from __future__ import annotations

import time

import pytest
from django.core.cache import cache
from django.test import Client, TestCase

from apps.contact.models import ContactMessage


@pytest.mark.django_db
class ContactViewTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def _payload(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": "Test Kullanıcı",
            "email": "TEST@EXAMPLE.ORG",
            "subject": "Kaynak önerisi",
            "message": "Yeni bir kaynak öneriyorum.",
            "privacy_accepted": "on",
            "started_at": str(time.time() - 5),
            "website": "",
        }
        payload.update(overrides)
        return payload

    def test_contact_page_is_public_noindex_without_account_language(self) -> None:
        response = Client().get("/iletisim/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "İletişim")
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'name="website"')
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_contact_post_creates_admin_inbox_message(self) -> None:
        response = Client().post("/iletisim/", self._payload(), HTTP_USER_AGENT="pytest-agent")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mesajınız alındı")
        message = ContactMessage.objects.get()
        self.assertEqual(message.email, "test@example.org")
        self.assertEqual(message.status, ContactMessage.Status.NEW)
        self.assertTrue(message.privacy_accepted)
        self.assertTrue(message.ip_hash)
        self.assertEqual(message.user_agent, "pytest-agent")

    def test_contact_honeypot_blocks_spam_without_saving(self) -> None:
        response = Client().post("/iletisim/", self._payload(website="https://spam.example"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mesaj gönderilemedi")
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_contact_rate_limit_returns_429(self) -> None:
        client = Client(REMOTE_ADDR="203.0.113.10")
        for index in range(5):
            response = client.post("/iletisim/", self._payload(email=f"user{index}@example.org"))
            self.assertEqual(response.status_code, 200)

        response = client.post("/iletisim/", self._payload(email="last@example.org"))

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Çok fazla istek gönderildi", status_code=429)
