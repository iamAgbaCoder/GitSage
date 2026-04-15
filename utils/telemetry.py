import locale
import platform
import threading
from typing import Optional

import requests

from utils import __version__

# Analytics Configuration
TELEMETRY_ENDPOINT = "https://gitsage-api.up.railway.app/v1/telemetry/track"


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
        requests.post(TELEMETRY_ENDPOINT, json=payload, timeout=2)
    except Exception:
        pass


def track_event(event_name: str, config: dict, properties: Optional[dict] = None):
    """Public entry point for anonymous telemetry."""
    properties = properties or {}
    user_id = config.get("anonymous_id", "unknown")

    threading.Thread(
        target=_send_event, args=(event_name, properties, user_id), daemon=True
    ).start()
