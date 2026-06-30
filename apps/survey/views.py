from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apps.survey.forms import GrantSurveyForm
from apps.survey.matcher import match_calls, profile_from_cleaned_data


@require_http_methods(["GET", "POST"])
def grant_survey(request: HttpRequest) -> HttpResponse:
    form = GrantSurveyForm(request.POST or None)
    matches = []
    if request.method == "POST" and form.is_valid():
        matches = match_calls(profile_from_cleaned_data(form.cleaned_data))

    return render(
        request,
        "pages/grant_survey.html",
        {
            "page_title": "Hibe Anketi | HibeRota",
            "meta_description": "Rolünüze, ülkenize ve ilgi alanınıza göre yayınlanmış hibe çağrılarını eşleştirin.",
            "canonical_path": "/hibe-anketi/",
            "robots": "noindex,follow",
            "form": form,
            "matches": matches,
            "submitted": request.method == "POST",
        },
    )
