from __future__ import annotations

from typing import Any

from django.conf import settings
from django.http import HttpRequest


def analytics_settings(request: HttpRequest) -> dict[str, Any]:
    cmp_script_url = getattr(settings, "CMP_SCRIPT_URL", "")
    if not cmp_script_url.startswith("https://"):
        cmp_script_url = ""
    adsense_client_id = getattr(settings, "ADSENSE_CLIENT_ID", "")
    adsense_ready = bool(getattr(settings, "ADSENSE_ENABLED", False)) and adsense_client_id.startswith("ca-pub-")
    return {
        "ga4_measurement_id": getattr(settings, "GA4_MEASUREMENT_ID", ""),
        "cmp_enabled": bool(getattr(settings, "CMP_ENABLED", False)),
        "cmp_provider_name": getattr(settings, "CMP_PROVIDER_NAME", ""),
        "cmp_script_url": cmp_script_url,
        "adsense_ready": adsense_ready,
        "adsense_client_id": adsense_client_id if adsense_ready else "",
        "adsense_slots": {
            "call_list_top": getattr(settings, "ADSENSE_SLOT_CALL_LIST_TOP", ""),
            "call_detail_inline": getattr(settings, "ADSENSE_SLOT_CALL_DETAIL_INLINE", ""),
        },
        "google_site_verification": getattr(settings, "GOOGLE_SITE_VERIFICATION", ""),
        "bing_site_verification": getattr(settings, "BING_SITE_VERIFICATION", ""),
    }
