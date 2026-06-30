from __future__ import annotations

import secrets
from collections.abc import Callable
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest, HttpResponseBase


class SecurityHeadersMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        request.csp_nonce = secrets.token_urlsafe(16)  # type: ignore[attr-defined]
        response = self.get_response(request)
        if not getattr(settings, "SECURITY_HEADERS_ENABLED", True):
            return response

        csp_header = (
            "Content-Security-Policy-Report-Only"
            if getattr(settings, "SECURITY_CSP_REPORT_ONLY", False)
            else "Content-Security-Policy"
        )
        response.setdefault(csp_header, build_content_security_policy(request))
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("Permissions-Policy", build_permissions_policy())
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if not _is_embed_request(request):
            response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        if getattr(settings, "STAGING_ROBOTS_NOINDEX", False):
            response.setdefault("X-Robots-Tag", "noindex, nofollow")
        return response


def build_content_security_policy(request: HttpRequest) -> str:
    nonce = getattr(request, "csp_nonce", "")
    script_sources = [
        "'self'",
        f"'nonce-{nonce}'",
        "https://cdn.jsdelivr.net",
        "https://www.googletagmanager.com",
        "https://pagead2.googlesyndication.com",
    ]
    if cmp_origin := _https_origin(getattr(settings, "CMP_SCRIPT_URL", "")):
        script_sources.append(cmp_origin)

    directives = [
        ("default-src", ["'self'"]),
        ("script-src", script_sources),
        ("style-src", ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"]),
        ("img-src", ["'self'", "data:", "https:"]),
        ("font-src", ["'self'", "data:", "https://cdn.jsdelivr.net"]),
        ("connect-src", ["'self'", "https://www.google-analytics.com", "https://region1.google-analytics.com"]),
        ("frame-src", ["'self'", "https://googleads.g.doubleclick.net"]),
        ("object-src", ["'none'"]),
        ("base-uri", ["'self'"]),
        ("form-action", ["'self'"]),
        ("frame-ancestors", ["'none'"]),
    ]
    if getattr(settings, "SECURITY_CSP_UPGRADE_INSECURE_REQUESTS", not settings.DEBUG):
        directives.append(("upgrade-insecure-requests", []))

    return "; ".join(_format_directive(name, values) for name, values in directives)


def build_permissions_policy() -> str:
    policies = [
        "accelerometer=()",
        "camera=()",
        "geolocation=()",
        "gyroscope=()",
        "magnetometer=()",
        "microphone=()",
        "payment=()",
        "usb=()",
    ]
    return ", ".join(policies)


def _format_directive(name: str, values: list[str]) -> str:
    if not values:
        return name
    return f"{name} {' '.join(values)}"


def _https_origin(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _is_embed_request(request: HttpRequest) -> bool:
    return request.path.endswith("/embed/")
