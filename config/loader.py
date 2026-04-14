"""
GitSage Configuration and Secure Authentication Storage.

Two separate files are used intentionally:
  ~/.git-sage.json   — general user preferences (style, telemetry, etc.)
  ~/.gitsage_auth    — API key only, chmod 600 on Unix systems
"""

from __future__ import annotations

import json
import os
import stat
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

# ── Paths ──────────────────────────────────────────────────────────────────
CONFIG_PATH = Path.home() / ".git-sage.json"
AUTH_FILE = Path.home() / ".gitsage_auth"

# ── Defaults ───────────────────────────────────────────────────────────────
DEFAULT_CONFIG: Dict[str, Any] = {
    "auto_commit": False,
    "max_length": 72,
    "style": "conventional",
    "telemetry": True,
    "anonymous_id": None,
}


# ── Config helpers ─────────────────────────────────────────────────────────


def load_config() -> Dict[str, Any]:
    """Load user preferences from ~/.git-sage.json, merging with defaults."""
    config = DEFAULT_CONFIG.copy()

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception:
            pass  # Corrupt file — fall back to defaults silently

    # Generate a stable anonymous ID on first run
    if not config.get("anonymous_id"):
        config["anonymous_id"] = str(uuid.uuid4())
        save_config(config)

    return config


def save_config(config: Dict[str, Any]):
    """Persist user preferences to ~/.git-sage.json."""
    # Never leak the API key into the general config file
    sanitised = {k: v for k, v in config.items() if k != "api_key"}
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(sanitised, f, indent=4)
    except OSError:
        pass


# ── Secure API key helpers ─────────────────────────────────────────────────


def load_api_key() -> Optional[str]:
    """
    Read the GitSage API key from the secure auth file.

    Returns None if the file doesn't exist or is unreadable.
    """
    if not AUTH_FILE.exists():
        return None
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            key = data.get("api_key", "").strip()
            return key if key else None
    except Exception:
        return None


def save_api_key(api_key: str):
    """
    Write the API key to ~/.gitsage_auth and set file permissions to 600
    (owner read/write only) on Unix systems to prevent other processes or
    users from reading it.
    """
    try:
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump({"api_key": api_key.strip()}, f)
        # Restrict permissions — silently skipped on Windows
        os.chmod(AUTH_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def delete_api_key():
    """Remove the stored API key (used by `gitsage auth --logout`)."""
    try:
        AUTH_FILE.unlink(missing_ok=True)
    except OSError:
        pass
