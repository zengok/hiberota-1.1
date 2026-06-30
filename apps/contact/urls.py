from __future__ import annotations

from django.urls import path

from .views import contact

urlpatterns = [
    path("", contact, name="contact"),
]
