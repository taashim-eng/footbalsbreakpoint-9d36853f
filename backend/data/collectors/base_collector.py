"""
Abstract base class for all data collectors.

Every concrete collector inherits from BaseCollector and implements the
`collect()` method.  Caching is handled transparently via Parquet files
with a configurable time-to-live (TTL).
"""

from abc import ABC, abstractmethod
import pandas as pd
import os
import json
from datetime import datetime, timedelta


class BaseCollector(ABC):
    """Base class providing caching, logging, and a uniform interface."""

    def __init__(self, name: str, cache_dir: str, ttl_hours: int = 24):
        self.name = name
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        os.makedirs(cache_dir, exist_ok=True)

    # ── Public API ───────────────────────────────────────────────────────

    @abstractmethod
    def collect(self, force: bool = False) -> pd.DataFrame:
        """Fetch / scrape data.  If *force* is True, bypass the cache."""
        pass

    # ── Cache helpers ────────────────────────────────────────────────────

    def _cache_path(self, key: str) -> str:
        """Return the filesystem path for a cached Parquet file."""
        return os.path.join(self.cache_dir, f"{self.name}_{key}.parquet")

    def _is_cache_valid(self, key: str) -> bool:
        """Check whether a cached file exists and is younger than the TTL."""
        path = self._cache_path(key)
        if not os.path.exists(path):
            return False
        modified = datetime.fromtimestamp(os.path.getmtime(path))
        return (datetime.now() - modified) < timedelta(hours=self.ttl_hours)

    def _read_cache(self, key: str) -> pd.DataFrame:
        """Read a cached Parquet file and return it as a DataFrame."""
        return pd.read_parquet(self._cache_path(key))

    def _write_cache(self, df: pd.DataFrame, key: str):
        """Persist a DataFrame to the cache as a Parquet file."""
        df.to_parquet(self._cache_path(key), index=False)

    # ── Logging ──────────────────────────────────────────────────────────

    def _log(self, msg: str):
        """Simple prefixed log message."""
        print(f"[{self.name}] {msg}")
