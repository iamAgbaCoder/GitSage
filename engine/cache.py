import hashlib
import json
import os
from dataclasses import asdict
from typing import Optional
from .models import CommitResult


class GitSageCache:
    """
    High-performance local caching system for AI commit intelligence.
    
    Uses SHA-256 hashes of git diffs to avoid redundant API calls.
    Maintains a FIFO limit of 50 entries to keep the cache file small.
    """
    def __init__(self, cache_file: str = ".gitsage_cache"):
        """
        Initialize the cache.
        
        Args:
            cache_file (str): The path to the local cache storage file.
        """
        self.cache_file = cache_file

    def _get_hash(self, content: str) -> str:
        """
        Compute a unique SHA-256 hash for the given content.
        
        Args:
            content (str): The text content (usually a git diff).
            
        Returns:
            str: The hexadecimal hash string.
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, diff_content: str) -> Optional[CommitResult]:
        """
        Attempt to retrieve a previous result from the cache.
        
        Args:
            diff_content (str): The git diff to check.
            
        Returns:
            Optional[CommitResult]: The cached result if found, otherwise None.
        """
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
        """
        Store a new intelligence result in the local cache.
        
        Args:
            diff_content (str): The git diff that generated the result.
            result (CommitResult): The intelligence result to store.
        """
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
