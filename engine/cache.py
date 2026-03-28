import hashlib
import json
import os
from dataclasses import asdict
from typing import Optional
from .models import CommitResult


class GitSageCache:
    def __init__(self, cache_file: str = ".gitsage_cache"):
        self.cache_file = cache_file

    def _get_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, diff_content: str) -> Optional[CommitResult]:
        if not os.path.exists(self.cache_file):
            return None

        diff_hash = self._get_hash(diff_content)
        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
                cached = data.get(diff_hash)
                if cached:
                    # Provide default for fields that may be missing from older cache entries
                    if "files_changed" not in cached:
                        cached["files_changed"] = []
                    return CommitResult(**cached)
        except (json.JSONDecodeError, Exception):
            pass
        return None

    def save(self, diff_content: str, result: CommitResult):
        diff_hash = self._get_hash(diff_content)
        data = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, Exception):
                pass

        data[diff_hash] = asdict(result)

        # Limit cache size to 50 entries to avoid bloating
        if len(data) > 50:
            # Simple FIFO removal (Python 3.7+ dicts maintain order)
            first_key = next(iter(data))
            del data[first_key]

        try:
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
