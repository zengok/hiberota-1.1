from __future__ import annotations

from django.contrib import admin
from django.test import SimpleTestCase

from apps.newsletter.admin import NewsletterDigestRunAdmin, NewsletterSubscriberAdmin, NewsletterSuppressionAdmin
from apps.newsletter.models import NewsletterDigestRun, NewsletterSubscriber, NewsletterSuppression


class NewsletterAdminTests(SimpleTestCase):
    def test_newsletter_subscriber_is_registered_in_admin(self) -> None:
        model_admin = admin.site._registry[NewsletterSubscriber]

        self.assertIsInstance(model_admin, NewsletterSubscriberAdmin)
        self.assertIn("status", model_admin.list_filter)
        self.assertIn("confirmation_token_hash", model_admin.readonly_fields)

    def test_newsletter_digest_run_is_registered_in_admin(self) -> None:
        model_admin = admin.site._registry[NewsletterDigestRun]

        self.assertIsInstance(model_admin, NewsletterDigestRunAdmin)
        self.assertIn("frequency", model_admin.list_filter)
        self.assertIn("sent_count", model_admin.readonly_fields)

    def test_newsletter_suppression_is_registered_in_admin(self) -> None:
        model_admin = admin.site._registry[NewsletterSuppression]

        self.assertIsInstance(model_admin, NewsletterSuppressionAdmin)
        self.assertIn("reason", model_admin.list_filter)
        self.assertIn("email_hash", model_admin.readonly_fields)
