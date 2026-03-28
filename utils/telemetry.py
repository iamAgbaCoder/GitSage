import threading
import requests
import platform
import uuid
from typing import Optional

# Anonymous Telemetry Configuration
# Users can disable this in config or via 'gitsage config --telemetry false'
TELEMETRY_ENDPOINT = "https://api.gitsage.dev/telemetry"

def _send_event(event_name: str, properties: dict):
    """Internal helper to send the event silently."""
    try:
        payload = {
            "event": event_name,
            "properties": {
                **properties,
                "os": platform.system(),
                "python_version": platform.python_version(),
            }
        }
        # Silent, non-blocking timeout
        requests.post(TELEMETRY_ENDPOINT, json=payload, timeout=2)
    except Exception:
        # Telemetry should NEVER block or crash the user experience
        pass

def track_event(event_name: str, config: dict, properties: Optional[dict] = None):
    """
    Public entry point for anonymous telemetry.
    Runs in a background thread to ensure zero performance impact.
    """
    if not config.get("telemetry", True):
        return

    # Ensure we have an anonymous ID
    properties = properties or {}
    properties["anonymous_id"] = config.get("anonymous_id", "unknown")

    # Dispatch to background thread
    threading.Thread(
        target=_send_event,
        args=(event_name, properties),
        daemon=True
    ).start()
