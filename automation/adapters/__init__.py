from .contracts import (
    CrawlContext,
    DiscoveredItem,
    FetchResult,
    ParsedCall,
    ParsedEvidence,
    SourceAdapter,
)
from .eu_funding import EuFundingTendersAdapter
from .examples import AtomFeedAdapter, JsonApiAdapter, StaticHtmlAdapter
from .registry import AdapterNotRegisteredLookupError, get_adapter

__all__ = [
    "AdapterNotRegisteredLookupError",
    "AtomFeedAdapter",
    "CrawlContext",
    "DiscoveredItem",
    "FetchResult",
    "EuFundingTendersAdapter",
    "JsonApiAdapter",
    "ParsedCall",
    "ParsedEvidence",
    "SourceAdapter",
    "StaticHtmlAdapter",
    "get_adapter",
]
