from __future__ import annotations

from django.urls import path

from .views import newsletter_confirm, newsletter_manage, newsletter_preferences, newsletter_unsubscribe

urlpatterns = [
    path("", newsletter_preferences, name="newsletter-preferences"),
    path("onay/<str:token>/", newsletter_confirm, name="newsletter-confirm"),
    path("tercihler/<str:token>/", newsletter_manage, name="newsletter-manage"),
    path("abonelikten-cik/<str:token>/", newsletter_unsubscribe, name="newsletter-unsubscribe"),
]
