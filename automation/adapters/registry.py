from __future__ import annotations

from automation.adapters.contracts import SourceAdapter
from automation.adapters.examples import AtomFeedAdapter, JsonApiAdapter, StaticHtmlAdapter


class AdapterNotRegisteredLookupError(LookupError):
    pass


EXACT_ADAPTERS: dict[str, type[SourceAdapter]] = {
    JsonApiAdapter.key: JsonApiAdapter,
    AtomFeedAdapter.key: AtomFeedAdapter,
    StaticHtmlAdapter.key: StaticHtmlAdapter,
}

SUFFIX_ADAPTERS: tuple[tuple[str, type[SourceAdapter]], ...] = (
    ("_api_v1", JsonApiAdapter),
    ("_feed_v1", AtomFeedAdapter),
    ("_html_v1", StaticHtmlAdapter),
)


def get_adapter(adapter_key: str) -> SourceAdapter:
    adapter_class = EXACT_ADAPTERS.get(adapter_key)
    if adapter_class is not None:
        return adapter_class()

    for suffix, suffix_adapter_class in SUFFIX_ADAPTERS:
        if adapter_key.endswith(suffix):
            return suffix_adapter_class()

    raise AdapterNotRegisteredLookupError(f"No source adapter registered for {adapter_key}.")
