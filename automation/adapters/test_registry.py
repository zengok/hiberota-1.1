from __future__ import annotations

from django.test import SimpleTestCase

from automation.adapters.examples import AtomFeedAdapter, JsonApiAdapter, StaticHtmlAdapter
from automation.adapters.registry import AdapterNotRegisteredLookupError, get_adapter


class AdapterRegistryTests(SimpleTestCase):
    def test_resolves_exact_example_adapter_key(self) -> None:
        self.assertIsInstance(get_adapter("example_html_v1"), StaticHtmlAdapter)

    def test_resolves_catalog_style_suffix_keys(self) -> None:
        self.assertIsInstance(get_adapter("src-0001_html_v1"), StaticHtmlAdapter)
        self.assertIsInstance(get_adapter("src-0002_feed_v1"), AtomFeedAdapter)
        self.assertIsInstance(get_adapter("src-0003_api_v1"), JsonApiAdapter)

    def test_unknown_adapter_key_raises_clear_lookup_error(self) -> None:
        with self.assertRaises(AdapterNotRegisteredLookupError):
            get_adapter("src-0004_unknown_v1")
