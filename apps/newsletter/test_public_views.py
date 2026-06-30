from __future__ import annotations

import re
import time
from typing import cast

import pytest
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase
from django.utils import timezone

from apps.newsletter.models import NewsletterSubscriber, NewsletterSuppression
from apps.newsletter.services import suppress_email, token_hash


@pytest.mark.django_db
class NewsletterViewTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def _payload(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "email": "TEST@EXAMPLE.ORG",
            "frequency": NewsletterSubscriber.Frequency.WEEKLY,
            "consent_accepted": "on",
            "started_at": str(time.time() - 5),
            "website": "",
        }
        payload.update(overrides)
        return payload

    def test_newsletter_page_is_public_noindex_without_account_language(self) -> None:
        response = Client().get("/ebulten/")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "E-bülten tercihleri")
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, 'name="website"')
        self.assertNotIn("Giriş yap", content)
        self.assertNotIn("Üye ol", content)

    def test_subscribe_creates_pending_subscriber_and_sends_confirmation(self) -> None:
        response = Client().post("/ebulten/", self._payload(frequency=NewsletterSubscriber.Frequency.MONTHLY))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Abonelik isteğiniz alındı")
        subscriber = NewsletterSubscriber.objects.get()
        self.assertEqual(subscriber.email, "test@example.org")
        self.assertEqual(subscriber.frequency, NewsletterSubscriber.Frequency.MONTHLY)
        self.assertEqual(subscriber.status, NewsletterSubscriber.Status.PENDING)
        self.assertTrue(subscriber.confirmation_token_hash)
        self.assertTrue(subscriber.unsubscribe_token_hash)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/ebulten/onay/", mail.outbox[0].body)

    def test_confirmation_activates_subscription(self) -> None:
        Client().post("/ebulten/", self._payload())
        token = self._confirmation_token_from_outbox()

        response = Client().get(f"/ebulten/onay/{token}/")
        subscriber = NewsletterSubscriber.objects.get()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "aboneliğiniz onaylandı")
        self.assertEqual(subscriber.status, NewsletterSubscriber.Status.CONFIRMED)
        self.assertIsNotNone(subscriber.confirmed_at)

    def test_manage_preferences_and_unsubscribe_by_token(self) -> None:
        client = Client()
        raw_token = "-".join(["known", "management", "value"])
        subscriber = NewsletterSubscriber.objects.create(
            email="active@example.org",
            frequency=NewsletterSubscriber.Frequency.WEEKLY,
            status=NewsletterSubscriber.Status.CONFIRMED,
            consent_accepted=True,
            confirmation_token_hash=token_hash("confirm-token"),
            unsubscribe_token_hash=token_hash(raw_token),
            token_created_at=timezone.now(),
            confirmed_at=timezone.now(),
        )
        manage_token_hash = subscriber.unsubscribe_token_hash

        response = client.post(
            f"/ebulten/tercihler/{raw_token}/",
            {"frequency": NewsletterSubscriber.Frequency.DAILY},
        )
        subscriber.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(subscriber.frequency, NewsletterSubscriber.Frequency.DAILY)
        self.assertEqual(subscriber.unsubscribe_token_hash, manage_token_hash)

        response = client.get(f"/ebulten/abonelikten-cik/{raw_token}/")
        subscriber.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(subscriber.status, NewsletterSubscriber.Status.UNSUBSCRIBED)
        self.assertEqual(NewsletterSuppression.objects.count(), 1)

    def test_suppressed_email_gets_generic_response_without_email(self) -> None:
        suppress_email("blocked@example.org", NewsletterSuppression.Reason.MANUAL)

        response = Client().post("/ebulten/", self._payload(email="blocked@example.org"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Abonelik isteğiniz alındı")
        self.assertEqual(NewsletterSubscriber.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_honeypot_blocks_without_saving(self) -> None:
        response = Client().post("/ebulten/", self._payload(website="https://spam.example"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Abonelik isteği alınamadı")
        self.assertEqual(NewsletterSubscriber.objects.count(), 0)

    def test_rate_limit_returns_429(self) -> None:
        client = Client(REMOTE_ADDR="203.0.113.55")
        for index in range(5):
            response = client.post("/ebulten/", self._payload(email=f"user{index}@example.org"))
            self.assertEqual(response.status_code, 200)

        response = client.post("/ebulten/", self._payload(email="last@example.org"))

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Çok fazla istek gönderildi", status_code=429)

    def _confirmation_token_from_outbox(self) -> str:
        token = re.search(r"/ebulten/onay/([^/]+)/", cast(str, mail.outbox[0].body))
        if token is None:
            self.fail("Confirmation token missing from outbox.")
        return token.group(1)
