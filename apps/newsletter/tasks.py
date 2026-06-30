from __future__ import annotations

from config.celery import app

from apps.newsletter.services import send_due_digest


@app.task(name="newsletter.send_due_newsletter_digest")
def send_due_newsletter_digest(frequency: str) -> int:
    run = send_due_digest(frequency)
    return run.sent_count
