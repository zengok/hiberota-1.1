from __future__ import annotations

import time
from typing import Any

from django import forms
from django.core.exceptions import ValidationError

from apps.newsletter.models import NewsletterSubscriber

MIN_SUBMIT_SECONDS = 2


class NewsletterSubscribeForm(forms.Form):
    email = forms.EmailField(label="E-posta", max_length=254)
    frequency = forms.ChoiceField(
        label="Gönderim sıklığı",
        choices=NewsletterSubscriber.Frequency.choices,
        initial=NewsletterSubscriber.Frequency.WEEKLY,
    )
    consent_accepted = forms.BooleanField(label="E-bülten almak için açık izin veriyorum", required=True)
    website = forms.CharField(label="", required=False, widget=forms.HiddenInput)
    started_at = forms.FloatField(label="", required=False, widget=forms.HiddenInput)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["started_at"].initial = time.time()
        for name, field in self.fields.items():
            if name in {"website", "started_at"}:
                continue
            field.widget.attrs["class"] = "form-check-input" if name == "consent_accepted" else "form-control"

    def clean_email(self) -> str:
        return self.cleaned_data["email"].strip().lower()

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean() or {}
        if cleaned_data.get("website"):
            raise ValidationError("Abonelik isteği alınamadı. Lütfen tekrar deneyin.")
        started_at = cleaned_data.get("started_at")
        if not isinstance(started_at, float) or time.time() - started_at < MIN_SUBMIT_SECONDS:
            raise ValidationError("Abonelik isteği alınamadı. Lütfen tekrar deneyin.")
        return cleaned_data


class NewsletterPreferenceForm(forms.Form):
    frequency = forms.ChoiceField(label="Gönderim sıklığı", choices=NewsletterSubscriber.Frequency.choices)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["frequency"].widget.attrs["class"] = "form-control"
