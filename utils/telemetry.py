import locale
import platform
import threading
from typing import Optional

import requests

from utils import __version__

from config.remote import get_remote_config

# Analytics Configuration


def _send_event(event_type: str, properties: dict, user_id: str):
    """Internal helper to send a telemetry event silently."""
    try:
        payload = {
            "event_type": event_type,
            "source": "cli",
            "user_id": user_id,
            "metadata": {
                **properties,
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "python_version": getattr(platform, "python_version", lambda: "unknown")(),
                "app_version": __version__,
                "language": (locale.getlocale()[0] if hasattr(locale, "getlocale") else None)
                or "unknown",
            },
        }

        remote_config = get_remote_config()
        api_base_url = remote_config.get(
            "api_base_url", "https://gitsage-api.up.railway.app"
        ).rstrip("/")
        endpoint = f"{api_base_url}/v1/telemetry/track"

        requests.post(endpoint, json=payload, timeout=2)
    except Exception:
        pass


def track_event(event_name: str, config: dict, properties: Optional[dict] = None):
    """Public entry point for anonymous telemetry."""
    properties = properties or {}
    user_id = config.get("anonymous_id", "unknown")

    threading.Thread(
        target=_send_event, args=(event_name, properties, user_id), daemon=True
    ).start()
