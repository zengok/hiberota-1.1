from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apps.contact.forms import ContactForm
from apps.contact.services import create_contact_message, is_rate_limited
from apps.core.views import too_many_requests


@require_http_methods(["GET", "POST"])
def contact(request: HttpRequest) -> HttpResponse:
    form = ContactForm(request.POST or None)
    submitted = False
    if request.method == "POST" and form.is_valid():
        if is_rate_limited(request, form.cleaned_data["email"]):
            return too_many_requests(request)
        create_contact_message(request, form.cleaned_data)
        form = ContactForm()
        submitted = True

    return render(
        request,
        "pages/contact.html",
        {
            "page_title": "İletişim | HibeRota",
            "meta_description": "HibeRota ekibine güvenli iletişim formuyla ulaşın.",
            "canonical_path": "/iletisim/",
            "robots": "noindex,follow",
            "form": form,
            "submitted": submitted,
        },
    )
