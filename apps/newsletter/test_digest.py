from __future__ import annotations

from datetime import datetime, time, timedelta

import pytest
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.calls.models import GrantCall
from apps.institutions.models import Country, Institution
from apps.newsletter.models import NewsletterDigestRun, NewsletterSubscriber, NewsletterSuppression
from apps.newsletter.services import management_token_for, send_due_digest, suppress_email, token_hash
from apps.newsletter.tasks import send_due_newsletter_digest
from apps.sources.models import Source
from apps.taxonomy.models import AudienceType


@pytest.mark.django_db
@override_settings(SITE_BASE_URL="https://hiberota.example")
class NewsletterDigestTests(TestCase):
    def setUp(self) -> None:
        self.now = timezone.make_aware(datetime(2026, 6, 26, 9, 0, 0))
        self.country = Country.objects.create(code="TR", name_tr="Türkiye", name_en="Turkey")
        self.audience = AudienceType.objects.create(key="ogrenci", name_tr="Öğrenci", name_en="Student")
        self.institution = Institution.objects.create(country=self.country, name="Kurum", slug="kurum")
        self.source = Source.objects.create(
            institution=self.institution,
            name="Kaynak",
            base_url="https://example.org",
            listing_url="https://example.org/calls",
            source_type=Source.SourceType.HTML,
            adapter_key="newsletter-digest-source",
        )

    def _subscriber(self, *, frequency: str = NewsletterSubscriber.Frequency.WEEKLY) -> NewsletterSubscriber:
        subscriber = NewsletterSubscriber.objects.create(
            email="confirmed@example.org",
            frequency=frequency,
            status=NewsletterSubscriber.Status.CONFIRMED,
            consent_accepted=True,
            confirmation_token_hash=token_hash("confirm"),
            unsubscribe_token_hash=token_hash("unsubscribe"),
            token_created_at=self.now,
            confirmed_at=self.now,
        )
        return subscriber

    def _call(self, *, published_at: datetime) -> GrantCall:
        call = GrantCall.objects.create(
            title="Haftalık Enerji Çağrısı",
            slug="haftalik-enerji-cagrisi",
            source=self.source,
            institution=self.institution,
            summary="Enerji desteği",
            official_url="https://example.org/call",
            canonical_source_url="https://example.org/call/canonical",
            fingerprint="newsletter-digest-call",
            first_seen_at=published_at,
            application_open_at=published_at,
            deadline_at=published_at + timedelta(days=30),
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            availability_status=GrantCall.AvailabilityStatus.OPEN,
            published_at=published_at,
        )
        call.countries.add(self.country)
        call.audiences.add(self.audience)
        return call

    def test_weekly_digest_sends_period_calls_to_confirmed_subscribers(self) -> None:
        subscriber = self._subscriber()
        self._call(published_at=timezone.make_aware(datetime(2026, 6, 20, 12, 0, 0)))

        run = send_due_digest(NewsletterSubscriber.Frequency.WEEKLY, now=self.now)

        self.assertEqual(run.status, NewsletterDigestRun.Status.COMPLETED)
        self.assertEqual(run.subscriber_count, 1)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.sent_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Haftalık Enerji Çağrısı", mail.outbox[0].body)
        self.assertIn("https://hiberota.example/cagrilar/haftalik-enerji-cagrisi-", mail.outbox[0].body)
        self.assertIn("/ebulten/tercihler/", mail.outbox[0].body)
        self.assertIn("/ebulten/abonelikten-cik/", mail.outbox[0].body)
        self.assertIsNotNone(management_token_for(subscriber))

    def test_digest_run_is_idempotent_for_same_period(self) -> None:
        self._subscriber()
        self._call(published_at=timezone.make_aware(datetime(2026, 6, 20, 12, 0, 0)))

        first_run = send_due_digest(NewsletterSubscriber.Frequency.WEEKLY, now=self.now)
        second_run = send_due_digest(NewsletterSubscriber.Frequency.WEEKLY, now=self.now)

        self.assertEqual(first_run.id, second_run.id)
        self.assertEqual(len(mail.outbox), 1)

    def test_digest_ignores_unconfirmed_subscribers(self) -> None:
        NewsletterSubscriber.objects.create(
            email="pending@example.org",
            frequency=NewsletterSubscriber.Frequency.WEEKLY,
            status=NewsletterSubscriber.Status.PENDING,
            consent_accepted=True,
            confirmation_token_hash=token_hash("confirm"),
            unsubscribe_token_hash=token_hash("unsubscribe"),
            token_created_at=self.now,
        )
        self._call(published_at=timezone.make_aware(datetime(2026, 6, 20, 12, 0, 0)))

        run = send_due_digest(NewsletterSubscriber.Frequency.WEEKLY, now=self.now)

        self.assertEqual(run.subscriber_count, 0)
        self.assertEqual(run.sent_count, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_digest_skips_suppressed_subscribers(self) -> None:
        subscriber = self._subscriber()
        suppress_email(subscriber.email, NewsletterSuppression.Reason.BOUNCE)
        self._call(published_at=timezone.make_aware(datetime(2026, 6, 20, 12, 0, 0)))

        run = send_due_digest(NewsletterSubscriber.Frequency.WEEKLY, now=self.now)

        self.assertEqual(run.subscriber_count, 1)
        self.assertEqual(run.sent_count, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_celery_task_returns_sent_count(self) -> None:
        self._subscriber(frequency=NewsletterSubscriber.Frequency.DAILY)
        current_day_start = timezone.make_aware(datetime.combine(timezone.now().date(), time.min))
        self._call(published_at=current_day_start - timedelta(hours=12))

        sent_count = send_due_newsletter_digest(NewsletterSubscriber.Frequency.DAILY)

        self.assertEqual(sent_count, 1)
