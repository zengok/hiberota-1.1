from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from apps.calls.detail import build_call_detail_path
from apps.calls.models import GrantCall
from apps.newsletter.models import NewsletterDigestRun, NewsletterSubscriber, NewsletterSuppression

RATE_LIMIT = 5
RATE_LIMIT_SECONDS = 3600
TOKEN_BYTES = 32
TOKEN_TTL_DAYS = 7
SIGNING_SALT = "-".join(["newsletter", "management"])


@dataclass(frozen=True)
class SubscriptionResult:
    subscriber: NewsletterSubscriber
    confirmation_url: str
    confirmation_code: str


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_newsletter_key(value: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), value.strip().lower().encode(), hashlib.sha256).hexdigest()


def client_ip_hash(request: HttpRequest) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    client_ip = forwarded_for.split(",", 1)[0].strip() or request.META.get("REMOTE_ADDR", "")
    return hash_newsletter_key(client_ip)


def token_hash(token: str) -> str:
    return hash_newsletter_key(token)


def is_rate_limited(request: HttpRequest, email: str) -> bool:
    keys = [f"newsletter:ip:{client_ip_hash(request)}", f"newsletter:email:{hash_newsletter_key(email)}"]
    limited = False
    for key in keys:
        if cache.add(key, 1, timeout=RATE_LIMIT_SECONDS):
            continue
        count = cache.incr(key)
        if count > RATE_LIMIT:
            limited = True
    return limited


def subscribe(request: HttpRequest, cleaned_data: dict[str, Any]) -> SubscriptionResult:
    email = normalize_email(cleaned_data["email"])
    raw_confirmation_token = secrets.token_urlsafe(TOKEN_BYTES)
    raw_unsubscribe_token = secrets.token_urlsafe(TOKEN_BYTES)
    now = timezone.now()
    if is_suppressed(email):
        return SubscriptionResult(
            subscriber=_unsaved_suppressed_subscriber(email, cleaned_data["frequency"]),
            confirmation_url="",
            confirmation_code="",
        )
    subscriber, _created = NewsletterSubscriber.objects.update_or_create(
        email=email,
        defaults={
            "frequency": cleaned_data["frequency"],
            "status": NewsletterSubscriber.Status.PENDING,
            "consent_accepted": cleaned_data["consent_accepted"],
            "confirmation_token_hash": token_hash(raw_confirmation_token),
            "unsubscribe_token_hash": token_hash(raw_unsubscribe_token),
            "token_created_at": now,
            "confirmed_at": None,
            "unsubscribed_at": None,
            "ip_hash": client_ip_hash(request),
        },
    )
    confirmation_url = request.build_absolute_uri(
        reverse("newsletter-confirm", kwargs={"token": raw_confirmation_token})
    )
    send_confirmation_email(email, confirmation_url)
    return SubscriptionResult(
        subscriber=subscriber,
        confirmation_url=confirmation_url,
        confirmation_code=raw_confirmation_token,
    )


def send_confirmation_email(email: str, confirmation_url: str) -> None:
    send_mail(
        subject="HibeRota e-bülten aboneliğinizi onaylayın",
        message=(
            "HibeRota e-bülten aboneliğinizi tamamlamak için bağlantıyı açın:\n\n"
            f"{confirmation_url}\n\n"
            "Bu isteği siz yapmadıysanız bu e-postayı yok sayabilirsiniz."
        ),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.invalid"),
        recipient_list=[email],
        fail_silently=True,
    )


def confirm_subscription(token: str) -> NewsletterSubscriber | None:
    subscriber = _subscriber_by_token("confirmation_token_hash", token)
    if subscriber is None or _token_expired(subscriber):
        return None
    subscriber.status = NewsletterSubscriber.Status.CONFIRMED
    subscriber.confirmed_at = timezone.now()
    subscriber.unsubscribed_at = None
    subscriber.save(update_fields=["status", "confirmed_at", "unsubscribed_at", "updated_at"])
    return subscriber


def unsubscribe(token: str) -> NewsletterSubscriber | None:
    subscriber = subscriber_by_management_token(token)
    if subscriber is None:
        return None
    subscriber.status = NewsletterSubscriber.Status.UNSUBSCRIBED
    subscriber.unsubscribed_at = timezone.now()
    subscriber.save(update_fields=["status", "unsubscribed_at", "updated_at"])
    suppress_email(subscriber.email, NewsletterSuppression.Reason.UNSUBSCRIBE)
    return subscriber


def suppress_email(email: str, reason: str, note: str = "") -> NewsletterSuppression:
    suppression, _created = NewsletterSuppression.objects.update_or_create(
        email_hash=hash_newsletter_key(normalize_email(email)),
        defaults={"reason": reason, "note": note[:300]},
    )
    return suppression


def is_suppressed(email: str) -> bool:
    return NewsletterSuppression.objects.filter(email_hash=hash_newsletter_key(normalize_email(email))).exists()


def update_preferences(token: str, frequency: str) -> NewsletterSubscriber | None:
    subscriber = subscriber_by_management_token(token)
    if subscriber is None or subscriber.status != NewsletterSubscriber.Status.CONFIRMED:
        return None
    subscriber.frequency = frequency
    subscriber.save(update_fields=["frequency", "updated_at"])
    return subscriber


def subscriber_by_management_token(token: str) -> NewsletterSubscriber | None:
    signed_subscriber = _subscriber_by_signed_token(token)
    if signed_subscriber is not None:
        return signed_subscriber
    return _subscriber_by_token("unsubscribe_token_hash", token)


def management_token_for(subscriber: NewsletterSubscriber) -> str:
    return signing.Signer(salt=SIGNING_SALT).sign(str(subscriber.pk))


def management_url_for(subscriber: NewsletterSubscriber) -> str:
    return _absolute_url(reverse("newsletter-manage", kwargs={"token": management_token_for(subscriber)}))


def unsubscribe_url_for(subscriber: NewsletterSubscriber) -> str:
    return _absolute_url(reverse("newsletter-unsubscribe", kwargs={"token": management_token_for(subscriber)}))


def send_due_digest(frequency: str, now: datetime | None = None) -> NewsletterDigestRun:
    period_start, period_end = _period_bounds(frequency, now or timezone.now())
    with transaction.atomic():
        run, created = NewsletterDigestRun.objects.get_or_create(
            frequency=frequency,
            period_start=period_start,
            period_end=period_end,
            defaults={"status": NewsletterDigestRun.Status.RUNNING},
        )
        if not created and run.status == NewsletterDigestRun.Status.COMPLETED:
            return run

    try:
        calls = list(_digest_calls(period_start, period_end))
        subscribers = list(
            NewsletterSubscriber.objects.filter(
                status=NewsletterSubscriber.Status.CONFIRMED,
                frequency=frequency,
                consent_accepted=True,
            ).order_by("email")
        )
        sent_count = 0
        if calls:
            for subscriber in subscribers:
                if is_suppressed(subscriber.email):
                    continue
                send_digest_email(subscriber, calls, period_start, period_end)
                sent_count += 1
        run.status = NewsletterDigestRun.Status.COMPLETED
        run.subscriber_count = len(subscribers)
        run.call_count = len(calls)
        run.sent_count = sent_count
        run.error_message = ""
        run.save(
            update_fields=[
                "status",
                "subscriber_count",
                "call_count",
                "sent_count",
                "error_message",
                "updated_at",
            ]
        )
    except Exception as exc:
        run.status = NewsletterDigestRun.Status.FAILED
        run.error_message = str(exc)[:500]
        run.save(update_fields=["status", "error_message", "updated_at"])
        raise
    return run


def send_digest_email(
    subscriber: NewsletterSubscriber,
    calls: list[GrantCall],
    period_start: datetime,
    period_end: datetime,
) -> None:
    lines = [
        "HibeRota e-bülteniniz",
        "",
        f"Dönem: {period_start:%Y-%m-%d} - {period_end:%Y-%m-%d}",
        "",
    ]
    for call in calls[:10]:
        lines.extend(
            [
                f"- {call.title}",
                f"  {_absolute_url(build_call_detail_path(call))}",
            ]
        )
    lines.extend(
        [
            "",
            f"Tercihleri yönet: {management_url_for(subscriber)}",
            f"Tek tıkla abonelikten çık: {unsubscribe_url_for(subscriber)}",
        ]
    )
    send_mail(
        subject="HibeRota e-bülteniniz",
        message="\n".join(lines),
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.invalid"),
        recipient_list=[subscriber.email],
        fail_silently=True,
    )


def _subscriber_by_token(field_name: str, token: str) -> NewsletterSubscriber | None:
    if not token:
        return None
    return NewsletterSubscriber.objects.filter(**{field_name: token_hash(token)}).first()


def _token_expired(subscriber: NewsletterSubscriber) -> bool:
    if subscriber.token_created_at is None:
        return True
    return subscriber.token_created_at < timezone.now() - timedelta(days=TOKEN_TTL_DAYS)


def _subscriber_by_signed_token(token: str) -> NewsletterSubscriber | None:
    try:
        raw_id = signing.Signer(salt=SIGNING_SALT).unsign(token)
    except signing.BadSignature:
        return None
    if not raw_id.isdigit():
        return None
    return NewsletterSubscriber.objects.filter(pk=int(raw_id)).first()


def _unsaved_suppressed_subscriber(email: str, frequency: str) -> NewsletterSubscriber:
    return NewsletterSubscriber(
        email=email,
        frequency=frequency,
        status=NewsletterSubscriber.Status.UNSUBSCRIBED,
        consent_accepted=False,
    )


def _period_bounds(frequency: str, now: datetime) -> tuple[datetime, datetime]:
    current_day_start = timezone.make_aware(datetime.combine(now.date(), time.min))
    if frequency == NewsletterSubscriber.Frequency.DAILY:
        return current_day_start - timedelta(days=1), current_day_start
    if frequency == NewsletterSubscriber.Frequency.MONTHLY:
        month_start = current_day_start.replace(day=1)
        previous_month_end = month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)
        return previous_month_start, month_start
    week_start = current_day_start - timedelta(days=current_day_start.weekday())
    return week_start - timedelta(days=7), week_start


def _digest_calls(period_start: datetime, period_end: datetime) -> QuerySet[GrantCall]:
    return (
        GrantCall.objects.filter(
            workflow_status=GrantCall.WorkflowStatus.PUBLISHED,
            published_at__gte=period_start,
            published_at__lte=period_end,
        )
        .select_related("institution")
        .order_by("-published_at", "-first_seen_at")[:10]
    )


def _absolute_url(path: str) -> str:
    return f"{settings.SITE_BASE_URL.rstrip('/')}{path}"
