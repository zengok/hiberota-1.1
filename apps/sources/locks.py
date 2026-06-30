from __future__ import annotations

from dataclasses import dataclass

from django.core.cache import cache


@dataclass(frozen=True, slots=True)
class CrawlLock:
    source_id: int
    ttl_seconds: int = 30 * 60

    @property
    def key(self) -> str:
        return f"crawl-lock:source:{self.source_id}"

    def acquire(self) -> bool:
        return bool(cache.add(self.key, "locked", timeout=self.ttl_seconds))

    def release(self) -> None:
        cache.delete(self.key)
