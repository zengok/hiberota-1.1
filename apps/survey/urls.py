from __future__ import annotations

from django.urls import path

from .views import grant_survey

urlpatterns = [
    path("", grant_survey, name="grant-survey"),
]
