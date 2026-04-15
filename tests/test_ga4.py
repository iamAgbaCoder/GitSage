"""Tests for utils.telemetry — fires events on a daemon thread, never blocks."""

from __future__ import annotations

import time
from unittest.mock import patch

from utils.telemetry import track_event


def test_track_event_fires_even_when_telemetry_disabled():
    config = {"telemetry": False, "anonymous_id": "test-id"}
    fired: list[str] = []

    def fake_send(event_type: str, _props: dict, _user_id: str):
        fired.append(event_type)

    with patch("utils.telemetry._send_event", side_effect=fake_send):
        track_event("test_event", config)
        # Give the daemon thread a moment to fire
        for _ in range(20):
            if fired:
                break
            time.sleep(0.05)

    assert fired == ["test_event"]


def test_track_event_fires_daemon_thread_when_enabled():
    config = {"telemetry": True, "anonymous_id": "test-id"}
    fired: list[str] = []

    def fake_send(event_type: str, _props: dict, _user_id: str):
        fired.append(event_type)

    with patch("utils.telemetry._send_event", side_effect=fake_send):
        track_event("app_start", config)
        # Wait for the daemon thread to complete
        for _ in range(20):
            if fired:
                break
            time.sleep(0.05)

    assert fired == ["app_start"]


def test_track_event_passes_anonymous_id():
    config = {"telemetry": True, "anonymous_id": "abc-123"}
    received: list[dict] = []

    def capture(_event_type: str, props: dict, user_id: str):
        received.append({"props": props, "user_id": user_id})

    with patch("utils.telemetry._send_event", side_effect=capture):
        track_event("commit_success", config, {"provider": "gitsage"})
        for _ in range(20):
            if received:
                break
            time.sleep(0.05)

    assert received[0]["user_id"] == "abc-123"
    assert received[0]["props"]["provider"] == "gitsage"


def test_send_event_silently_swallows_network_errors():
    """_send_event must never raise even if the HTTP call fails."""
    from utils.telemetry import _send_event

    with patch("utils.telemetry.requests.post", side_effect=Exception("network down")):
        # Should not raise
        _send_event("test", {}, "x")
