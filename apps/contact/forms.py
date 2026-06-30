from __future__ import annotations

import time
from typing import Any

from django import forms
from django.core.exceptions import ValidationError

MIN_SUBMIT_SECONDS = 2


class ContactForm(forms.Form):
    name = forms.CharField(label="Ad soyad", max_length=160)
    email = forms.EmailField(label="E-posta", max_length=254)
    subject = forms.CharField(label="Konu", max_length=160)
    message = forms.CharField(label="Açıklama", max_length=4000, widget=forms.Textarea(attrs={"rows": 6}))
    privacy_accepted = forms.BooleanField(label="Gizlilik koşullarını kabul ediyorum", required=True)
    website = forms.CharField(label="", required=False, widget=forms.HiddenInput)
    started_at = forms.FloatField(label="", required=False, widget=forms.HiddenInput)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["started_at"].initial = time.time()
        for name, field in self.fields.items():
            if name in {"website", "started_at"}:
                continue
            field.widget.attrs["class"] = "form-check-input" if name == "privacy_accepted" else "form-control"

    def clean_email(self) -> str:
        return self.cleaned_data["email"].strip().lower()

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}
        if cleaned_data.get("website"):
            raise ValidationError("Mesaj gönderilemedi. Lütfen tekrar deneyin.")
        started_at = cleaned_data.get("started_at")
        if not isinstance(started_at, float) or time.time() - started_at < MIN_SUBMIT_SECONDS:
            raise ValidationError("Mesaj gönderilemedi. Lütfen tekrar deneyin.")
        return cleaned_data
