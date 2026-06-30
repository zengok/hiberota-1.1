from __future__ import annotations

from typing import Any, cast

from django import forms

from apps.calls.models import GrantCall
from apps.institutions.models import Country
from apps.taxonomy.models import AudienceType, OrganizationSize, ProgramType, Region, Sector, Theme

STATUS_CHOICES = [
    ("", "Açık ve yakındaki çağrılar"),
    (GrantCall.AvailabilityStatus.UPCOMING, "Gelecek"),
    (GrantCall.AvailabilityStatus.OPEN, "Açık"),
    (GrantCall.AvailabilityStatus.CLOSING_SOON, "Kapanmak üzere"),
    (GrantCall.AvailabilityStatus.CLOSED, "Kapalı"),
]


class GrantSurveyForm(forms.Form):
    q = forms.CharField(
        label="Aradığınız konu",
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Örn. enerji, Erasmus, Ar-Ge"}),
    )
    audience = forms.ModelChoiceField(
        label="Rolünüz / hedef kitleniz",
        queryset=AudienceType.objects.none(),
        required=True,
        empty_label="Seçin",
    )
    organization_size = forms.ModelChoiceField(
        label="Kurum ölçeği",
        queryset=OrganizationSize.objects.none(),
        required=False,
        empty_label="Fark etmez",
    )
    country = forms.ModelChoiceField(
        label="Ülke",
        queryset=Country.objects.none(),
        required=False,
        empty_label="Fark etmez",
    )
    region = forms.ModelChoiceField(
        label="Bölge",
        queryset=Region.objects.none(),
        required=False,
        empty_label="Fark etmez",
    )
    sector = forms.ModelChoiceField(
        label="Sektör",
        queryset=Sector.objects.none(),
        required=False,
        empty_label="Fark etmez",
    )
    theme = forms.ModelChoiceField(
        label="Tema",
        queryset=Theme.objects.none(),
        required=False,
        empty_label="Fark etmez",
    )
    program_type = forms.ModelChoiceField(
        label="Program türü",
        queryset=ProgramType.objects.none(),
        required=False,
        empty_label="Fark etmez",
    )
    availability_status = forms.ChoiceField(label="Çağrı durumu", choices=STATUS_CHOICES, required=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cast(forms.ModelChoiceField, self.fields["audience"]).queryset = AudienceType.objects.filter(
            is_active=True
        ).order_by("name_tr")
        cast(forms.ModelChoiceField, self.fields["organization_size"]).queryset = OrganizationSize.objects.filter(
            is_active=True
        ).order_by("name_tr")
        cast(forms.ModelChoiceField, self.fields["country"]).queryset = Country.objects.filter(is_active=True).order_by(
            "name_tr"
        )
        cast(forms.ModelChoiceField, self.fields["region"]).queryset = Region.objects.filter(is_active=True).order_by(
            "name_tr"
        )
        cast(forms.ModelChoiceField, self.fields["sector"]).queryset = Sector.objects.filter(is_active=True).order_by(
            "name_tr"
        )
        cast(forms.ModelChoiceField, self.fields["theme"]).queryset = Theme.objects.filter(is_active=True).order_by(
            "name_tr"
        )
        cast(forms.ModelChoiceField, self.fields["program_type"]).queryset = ProgramType.objects.filter(
            is_active=True
        ).order_by("name_tr")
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
