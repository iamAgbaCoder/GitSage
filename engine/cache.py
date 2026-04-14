"""
GitSage local result cache.

Stores AI intelligence results keyed by SHA-256(diff) so identical diffs
never trigger a redundant API round-trip.

Cache file location: ~/.gitsage_cache  (user home directory, not project dir)
This keeps the file out of version-controlled repos and makes it available
across all projects on the machine.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from .models import CommitResult

_DEFAULT_CACHE_PATH = Path.home() / ".gitsage_cache"
_MAX_ENTRIES = 100


class GitSageCache:
    """
    High-performance local cache for GitSage intelligence results.

    Uses SHA-256 hashes of (truncated) git diffs as keys.
    Maintains a FIFO cap of 100 entries so the file stays small.
    All I/O errors are silently swallowed — a cache miss is always safe.
    """

    def __init__(self, cache_path: Optional[Path] = None):
        self._path = cache_path or _DEFAULT_CACHE_PATH

    # ── Internal helpers ───────────────────────────────────────────────────

    def _hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _dump(self, data: dict):
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
        except Exception:
            pass

    # ── Public API ─────────────────────────────────────────────────────────

    def get(self, diff_content: str) -> Optional[CommitResult]:
        """Return the cached CommitResult for this diff, or None on miss."""
        data = self._load()
        entry = data.get(self._hash(diff_content))
        if not entry:
            return None
        try:
            entry.setdefault("files_changed", [])
            return CommitResult(**entry)
        except Exception:
            return None

    def save(self, diff_content: str, result: CommitResult):
        """Persist an intelligence result; evict oldest entry if over cap."""
        data = self._load()
        data[self._hash(diff_content)] = asdict(result)

        # FIFO eviction (Python 3.7+ dicts are insertion-ordered)
        while len(data) > _MAX_ENTRIES:
            data.pop(next(iter(data)))

        self._dump(data)

    def clear(self):
        """Wipe the entire cache file."""
        try:
            self._path.unlink(missing_ok=True)
        except Exception:
            pass
