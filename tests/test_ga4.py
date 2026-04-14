import locale
import os
import platform
import sys
import uuid

import requests

# Add root to sys.path to import from utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import __version__
from utils.telemetry import GA4_API_SECRET, GA4_MEASUREMENT_ID


def test_ga4_validation():
    """Validates the GA4 credentials and the new metadata fields."""
    url = f"https://www.google-analytics.com/debug/mp/collect?measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}"

    # We replicate the new payload structure from telemetry.py
    payload = {
        "client_id": str(uuid.uuid4()),
        "events": [
            {
                "name": "metadata_test_event",
                "params": {
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "architecture": platform.machine(),
                    "python_version": platform.python_version(),
                    "app_version": __version__,
                    "language": locale.getlocale()[0] or "unknown",
                    "engagement_time_msec": "1",
                    "test_mode": "true",
                    "custom_data_field": "test_value",
                },
            }
        ],
    }

    print("--- [TEST] GA4 Metadata Validation ---")
    print(f"Targeting: {GA4_MEASUREMENT_ID}")
    print(f"Metadata to send: Version {__version__}, Arch {platform.machine()}")

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()

        print(f"Status: {response.status_code}")

        if not result.get("validationMessages"):
            print("\n[SUCCESS] New enriched metadata payload is VALID!")
            print(f"Snapshot: Sent {len(payload['events'][0]['params'])} parameters.")
        else:
            print("\n[ERROR] Payload Validation Failed:")
            for msg in result["validationMessages"]:
                print(f"  - {msg.get('description')} (Field: {msg.get('fieldPath')})")

    except Exception as e:
        print(f"\n[CRITICAL] Request failed: {str(e)}")


if __name__ == "__main__":
    test_ga4_validation()
