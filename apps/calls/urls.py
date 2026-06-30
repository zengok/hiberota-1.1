from __future__ import annotations

from django.urls import path

from apps.calls.views import call_detail, call_embed, call_list, favorite_resolve

urlpatterns = [
    path("favoriler/coz/", favorite_resolve, name="favorite-resolve"),
    path("", call_list, name="call-list"),
    path("<slug:slug>-<int:pk>/embed/", call_embed, name="call-embed"),
    path("<slug:slug>-<int:pk>/", call_detail, name="call-detail"),
]
