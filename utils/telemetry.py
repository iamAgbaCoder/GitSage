import threading
import requests
import platform
import locale
from typing import Optional
from utils import __version__

# Google Analytics 4 Configuration
# Get your API secret from: GA4 Admin > Data Streams > [Stream] > Measurement Protocol API secrets
GA4_MEASUREMENT_ID = "G-R5TZNB9Q1R"
GA4_API_SECRET = "PSyfiE8bRh-iR5cpaERl0Q"
TELEMETRY_ENDPOINT = f"https://www.google-analytics.com/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"


def _send_event(event_name: str, properties: dict):
    """Internal helper to send a GA4 event silently."""
    try:
        payload = {
            "client_id": properties.get("anonymous_id", "unknown"),
            "events": [
                {
                    "name": event_name,
                    "params": {
                        **properties,
                        "os": platform.system(),
                        "os_version": platform.version(),
                        "architecture": platform.machine(),
                        "python_version": platform.python_version(),
                        "app_version": __version__,
                        "language": locale.getlocale()[0] or "unknown",
                        "engagement_time_msec": "1",
                    },
                }
            ],
        }
        requests.post(TELEMETRY_ENDPOINT, json=payload, timeout=2)
    except Exception:
        pass


def track_event(event_name: str, config: dict, properties: Optional[dict] = None):
    """Public entry point for anonymous telemetry."""
    if not config.get("telemetry", True):
        return

    properties = properties or {}
    properties["anonymous_id"] = config.get("anonymous_id", "unknown")

    threading.Thread(
        target=_send_event, args=(event_name, properties), daemon=True
    ).start()
