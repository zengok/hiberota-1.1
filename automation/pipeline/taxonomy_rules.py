from __future__ import annotations

import re
import unicodedata
from dataclasses import replace

from apps.calls.models import GrantCall
from apps.sources.models import Source

from automation.adapters.contracts import ParsedCall

AUDIENCE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "graduate_student",
        (
            "lisansüstü",
            "lisansustu",
            "yüksek lisans",
            "yuksek lisans",
            "doktora",
            "doctoral",
            "phd",
            "postgraduate",
        ),
    ),
    (
        "student",
        (
            "öğrenci",
            "ogrenci",
            "üniversite öğrenc",
            "universite ogrenc",
            "lisans öğrenc",
            "lisans ogrenc",
            "student",
        ),
    ),
    (
        "academic",
        (
            "akademisyen",
            "öğretim üyesi",
            "ogretim uyesi",
            "öğretim elemanı",
            "ogretim elemani",
            "faculty member",
            "academic",
        ),
    ),
    (
        "researcher",
        (
            "araştırmacı",
            "arastirmaci",
            "araştırma projesi",
            "arastirma projesi",
            "bilimsel araştırma",
            "bilimsel arastirma",
            "kutup araştır",
            "kutup arastir",
            "ar-ge",
            "arge",
            "r&d",
            "researcher",
            "research project",
        ),
    ),
    (
        "startup",
        (
            "startup",
            "start-up",
            "girişim",
            "girisim",
            "kuluçka",
            "kulucka",
            "incubation",
        ),
    ),
    (
        "entrepreneur",
        (
            "girişimci",
            "girisimci",
            "entrepreneur",
        ),
    ),
    (
        "sme",
        (
            "kobi",
            "kobİ",
            "küçük ve orta",
            "kucuk ve orta",
            "small and medium",
            "sme",
        ),
    ),
    (
        "company",
        (
            "firma",
            "şirket",
            "sirket",
            "işletme",
            "isletme",
            "sanayi kuruluş",
            "sanayi kurulus",
            "company",
            "business",
        ),
    ),
    (
        "ngo",
        (
            "stk",
            "sivil toplum",
            "dernek",
            "vakıf",
            "vakif",
            "ngo",
            "civil society",
        ),
    ),
    (
        "municipality",
        (
            "belediye",
            "municipality",
            "local authority",
        ),
    ),
    (
        "public_institution",
        (
            "kamu kurumu",
            "kamu kurum",
            "kamu kuruluş",
            "kamu kurulus",
            "public institution",
            "public body",
        ),
    ),
    (
        "consortium",
        (
            "konsorsiyum",
            "ortaklık",
            "ortaklik",
            "consortium",
            "partnership",
        ),
    ),
)


def apply_taxonomy_rules(*, source: Source, parsed_call: ParsedCall) -> ParsedCall:
    """Fill missing audience keys with conservative source/text-based rules."""
    if parsed_call.audience_keys:
        return parsed_call

    inferred_keys = infer_audience_keys(
        source=source,
        title=parsed_call.title,
        summary=parsed_call.summary,
        purpose=parsed_call.purpose,
        eligibility_text=parsed_call.eligibility_text,
        conditions_text=parsed_call.conditions_text,
        funding_text=parsed_call.funding_text,
        application_process_text=parsed_call.application_process_text,
    )
    if not inferred_keys:
        return parsed_call
    return replace(parsed_call, audience_keys=inferred_keys)


def infer_audience_keys_for_call(call: GrantCall) -> tuple[str, ...]:
    return infer_audience_keys(
        source=call.source,
        title=call.title,
        summary=call.summary,
        purpose=call.purpose,
        eligibility_text=call.eligibility_text,
        conditions_text=call.conditions_text,
        funding_text=call.funding_text,
        application_process_text=call.application_process_text,
    )


def infer_audience_keys(
    *,
    source: Source,
    title: str = "",
    summary: str = "",
    purpose: str = "",
    eligibility_text: str = "",
    conditions_text: str = "",
    funding_text: str = "",
    application_process_text: str = "",
) -> tuple[str, ...]:
    keys: list[str] = []
    keys.extend(_source_audience_hints(source))

    text = _normalise_text(
        " ".join(
            (
                title,
                summary,
                purpose,
                eligibility_text,
                conditions_text,
                funding_text,
                application_process_text,
                source.institution.name,
                source.name,
            )
        )
    )
    for key, patterns in AUDIENCE_RULES:
        if any(_contains_pattern(text, pattern) for pattern in patterns):
            keys.append(key)

    return tuple(dict.fromkeys(key for key in keys if key))


def _source_audience_hints(source: Source) -> list[str]:
    raw_hints = source.config_json.get("audience_hints", [])
    if not isinstance(raw_hints, list):
        return []
    return [str(key).strip() for key in raw_hints if str(key).strip()]


def _normalise_text(value: str) -> str:
    casefolded = value.casefold()
    ascii_value = unicodedata.normalize("NFKD", casefolded).encode("ascii", "ignore").decode("ascii")
    return f"{casefolded} {ascii_value}"


def _contains_pattern(text: str, pattern: str) -> bool:
    variants = _normalise_variants(pattern)
    if not variants:
        return False
    return any(re.search(rf"(?<!\w){re.escape(variant)}", text) is not None for variant in variants)


def _normalise_variants(value: str) -> tuple[str, ...]:
    casefolded = value.casefold().strip()
    ascii_value = unicodedata.normalize("NFKD", casefolded).encode("ascii", "ignore").decode("ascii").strip()
    return tuple(dict.fromkeys(variant for variant in (casefolded, ascii_value) if variant))
