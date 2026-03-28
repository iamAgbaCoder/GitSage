import json
from pathlib import Path
from typing import Dict, Any

CONFIG_PATH = Path.home() / ".git-sage.json"

DEFAULT_CONFIG = {
    "ai_provider": "gemini",
    "auto_commit": False,
    "max_length": 72,
    "style": "conventional",
    "telemetry": True,
    "anonymous_id": None,
}


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            user_config = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    except Exception:
        config = DEFAULT_CONFIG.copy()

    # Ensure anonymous_id is generated once
    if not config.get("anonymous_id"):
        import uuid

        config["anonymous_id"] = str(uuid.uuid4())
        save_config(config)

    return config


def save_config(config: Dict[str, Any]):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
