"""Tests for config.loader — preferences and secure API key storage."""

from __future__ import annotations

import json
import stat
import sys

import pytest

# ---------------------------------------------------------------------------
# Fixtures: redirect file paths away from the real home directory
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Patch CONFIG_PATH and AUTH_FILE to use tmp_path for every test."""
    import config.loader as loader

    monkeypatch.setattr(loader, "CONFIG_PATH", tmp_path / ".git-sage.json")
    monkeypatch.setattr(loader, "AUTH_FILE", tmp_path / ".gitsage_auth")
    yield


# ---------------------------------------------------------------------------
# load_config / save_config
# ---------------------------------------------------------------------------


def test_load_config_defaults_when_no_file():
    from config.loader import DEFAULT_CONFIG, load_config

    cfg = load_config()
    for key in DEFAULT_CONFIG:
        assert key in cfg


def test_load_config_merges_user_values(tmp_path, monkeypatch):
    import config.loader as loader

    cfg_path = tmp_path / ".git-sage.json"
    cfg_path.write_text(json.dumps({"style": "emoji", "max_length": 50}))
    monkeypatch.setattr(loader, "CONFIG_PATH", cfg_path)

    cfg = loader.load_config()
    assert cfg["style"] == "emoji"
    assert cfg["max_length"] == 50
    assert cfg["auto_commit"] is False  # default preserved


def test_save_config_does_not_write_api_key(tmp_path, monkeypatch):
    import config.loader as loader

    cfg_path = tmp_path / ".git-sage.json"
    monkeypatch.setattr(loader, "CONFIG_PATH", cfg_path)

    loader.save_config({"style": "conventional", "api_key": "gs_secret"})

    written = json.loads(cfg_path.read_text())
    assert "api_key" not in written
    assert written["style"] == "conventional"


def test_load_config_generates_anonymous_id(tmp_path, monkeypatch):
    import config.loader as loader

    monkeypatch.setattr(loader, "CONFIG_PATH", tmp_path / ".git-sage.json")
    cfg = loader.load_config()
    assert cfg["anonymous_id"] is not None
    assert len(cfg["anonymous_id"]) == 36  # UUID4 format


# ---------------------------------------------------------------------------
# save_api_key / load_api_key / delete_api_key
# ---------------------------------------------------------------------------


def test_save_and_load_api_key():
    from config.loader import load_api_key, save_api_key

    save_api_key("gs_test_key_abc123")
    assert load_api_key() == "gs_test_key_abc123"


def test_load_api_key_returns_none_when_missing():
    from config.loader import load_api_key

    assert load_api_key() is None


def test_delete_api_key():
    from config.loader import delete_api_key, load_api_key, save_api_key

    save_api_key("gs_to_delete")
    delete_api_key()
    assert load_api_key() is None


def test_save_api_key_trims_whitespace():
    from config.loader import load_api_key, save_api_key

    save_api_key("  gs_padded_key  ")
    assert load_api_key() == "gs_padded_key"


@pytest.mark.skipif(sys.platform == "win32", reason="chmod not enforced on Windows")
def test_auth_file_permissions(tmp_path, monkeypatch):
    import config.loader as loader

    monkeypatch.setattr(loader, "AUTH_FILE", tmp_path / ".gitsage_auth")
    loader.save_api_key("gs_secret")

    mode = stat.S_IMODE((tmp_path / ".gitsage_auth").stat().st_mode)
    assert mode == 0o600, f"Expected 0o600, got {oct(mode)}"
