import json
import time
from pathlib import Path
from typing import Any, Dict

import requests
from rich.console import Console

from utils import __version__

console = Console()

REMOTE_CONFIG_URL = "https://gitsage-ai.vercel.app/config.json"
CACHE_DIR = Path.home() / ".gitsage"
CACHE_FILE = CACHE_DIR / "config_cache.json"
CACHE_TTL = 3600  # 1 hour

DEFAULT_CONFIG: Dict[str, Any] = {
    "api_base_url": "https://gitsage-api.up.railway.app",
    "frontend_base_url": "https://gitsage-ai.vercel.app",
    "latest_version": "1.0.0",
    "min_supported_version": "1.0.0",
    "status": "ok",
    "features": {},
}


def _parse_version(version_str: str) -> tuple:
    """Parse a semver string into a tuple for easy comparison."""
    try:
        return tuple(map(int, version_str.strip("v").split(".")))
    except Exception:
        return (0, 0, 0)


def _load_cached_config() -> Dict[str, Any]:
    """Load configuration from the local cache file if it exists."""
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cached_config(config: Dict[str, Any]) -> None:
    """Save the configuration to the local cache file along with a timestamp."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {"timestamp": time.time(), "config": config}
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def _check_notices(config: Dict[str, Any]) -> None:
    """Print notices if system status is not ok or version is unsupported."""
    status = config.get("status", "ok")
    if status != "ok":
        console.print(
            f"[bold yellow]System Notice:[/bold yellow] GitSage API status is currently: {status}"
        )

    min_ver_str = config.get("min_supported_version", "1.0.0")
    min_ver = _parse_version(min_ver_str)
    current_ver = _parse_version(__version__)

    if current_ver < min_ver:
        console.print(
            f"[bold red]Warning:[/bold red] Your version ([bold]{__version__}[/bold]) is older "
            f"than the minimum supported version ([bold]{min_ver_str}[/bold]). Please update your CLI."
        )


def get_remote_config() -> Dict[str, Any]:
    """
    Fetch remote config from URL, using cache and fallback logic.
    Never raises an exception. Always returns a valid config dictionary.
    """
    cached_data = _load_cached_config()
    cached_config = cached_data.get("config", {})
    cached_time = cached_data.get("timestamp", 0)

    # Use cached config if it's valid and not expired
    if cached_config and (time.time() - cached_time < CACHE_TTL):
        _check_notices(cached_config)
        return cached_config

    try:
        # Attempt to fetch new config with a 5s timeout
        response = requests.get(REMOTE_CONFIG_URL, timeout=5)
        response.raise_for_status()
        new_config = response.json()

        # Merge with default to ensure required keys always exist
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(new_config)

        _save_cached_config(merged_config)
        _check_notices(merged_config)
        return merged_config

    except Exception:
        # Fetch or parsing failed
        # If we have a cached config (even if expired), use it as fallback
        if cached_config:
            _check_notices(cached_config)
            return cached_config

        # Absolute worst-case scenario: return defaults
        merged_defaults = DEFAULT_CONFIG.copy()
        _check_notices(merged_defaults)
        return merged_defaults
