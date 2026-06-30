from __future__ import annotations

from django.urls import path

from apps.institutions.views import institution_detail, institution_list

urlpatterns = [
    path("", institution_list, name="institution-list"),
    path("<slug:slug>/", institution_detail, name="institution-detail"),
]
