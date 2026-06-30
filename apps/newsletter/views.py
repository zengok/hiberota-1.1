from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.views import too_many_requests
from apps.newsletter.forms import NewsletterPreferenceForm, NewsletterSubscribeForm
from apps.newsletter.services import (
    confirm_subscription,
    is_rate_limited,
    subscribe,
    subscriber_by_management_token,
    unsubscribe,
    update_preferences,
)


@require_http_methods(["GET", "POST"])
def newsletter_preferences(request: HttpRequest) -> HttpResponse:
    form = NewsletterSubscribeForm(request.POST or None)
    submitted = False
    if request.method == "POST" and form.is_valid():
        if is_rate_limited(request, form.cleaned_data["email"]):
            return too_many_requests(request)
        subscribe(request, form.cleaned_data)
        form = NewsletterSubscribeForm()
        submitted = True

    return render(
        request,
        "pages/newsletter.html",
        {
            "page_title": "E-bülten Tercihleri | HibeRota",
            "meta_description": "HibeRota e-bültenine çift onayla abone olun ve gönderim sıklığını seçin.",
            "canonical_path": "/ebulten/",
            "robots": "noindex,follow",
            "form": form,
            "submitted": submitted,
        },
    )


@require_GET
def newsletter_confirm(request: HttpRequest, token: str) -> HttpResponse:
    subscriber = confirm_subscription(token)
    return _status_page(
        request,
        title="Abonelik onayı",
        message="E-bülten aboneliğiniz onaylandı." if subscriber else "Abonelik onayı geçersiz veya süresi dolmuş.",
    )


@require_http_methods(["GET", "POST"])
def newsletter_manage(request: HttpRequest, token: str) -> HttpResponse:
    subscriber = subscriber_by_management_token(token)
    form = NewsletterPreferenceForm(request.POST or None)
    updated = False
    if request.method == "POST" and form.is_valid():
        subscriber = update_preferences(token, form.cleaned_data["frequency"])
        updated = subscriber is not None
    else:
        if subscriber:
            form = NewsletterPreferenceForm(initial={"frequency": subscriber.frequency})

    return render(
        request,
        "pages/newsletter_manage.html",
        {
            "page_title": "E-bülten Yönetimi | HibeRota",
            "meta_description": "HibeRota e-bülten gönderim sıklığını yönetin.",
            "robots": "noindex,follow",
            "form": form,
            "subscriber": subscriber,
            "updated": updated,
            "token": token,
        },
    )


@require_GET
def newsletter_unsubscribe(request: HttpRequest, token: str) -> HttpResponse:
    subscriber = unsubscribe(token)
    return _status_page(
        request,
        title="Abonelikten çıkış",
        message="E-bülten aboneliğiniz sonlandırıldı." if subscriber else "Abonelikten çıkış bağlantısı geçersiz.",
    )


def _status_page(request: HttpRequest, *, title: str, message: str) -> HttpResponse:
    return render(
        request,
        "pages/newsletter_status.html",
        {
            "page_title": f"{title} | HibeRota",
            "meta_description": message,
            "robots": "noindex,follow",
            "status_title": title,
            "status_message": message,
        },
    )
