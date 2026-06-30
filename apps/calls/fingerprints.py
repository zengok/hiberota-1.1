from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime

TURKISH_TRANSLATION = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ş": "s",
        "Ş": "s",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
    }
)


def normalize_fingerprint_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.translate(TURKISH_TRANSLATION).casefold())
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


def build_duplicate_fingerprint(
    *,
    institution_id: int,
    title: str,
    deadline_at: datetime | None,
    canonical_source_url: str,  # Kept for backward-compatible callers; canonical URL is a separate duplicate layer.
) -> str:
    deadline_part = deadline_at.date().isoformat() if deadline_at else "no-deadline"
    payload = "|".join(
        [
            str(institution_id),
            normalize_fingerprint_text(title),
            deadline_part,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
