"""Configuração da aplicação (secção 5.3, 7)."""

import json
import os
from typing import Dict, Any


CONFIG_DIR = os.path.expanduser("~/.config/cardsync")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


DEFAULT_CONFIG = {
    "version": 1,
    "backend": "local",  # local | gdrive
    "local_base_dir": os.path.expanduser("~/.local/share/cardsync/drive"),
    "gdrive": {
        "client_secrets_path": "",
    },
    "wifi_only_raw": True,
    "raw_concurrency": 4,
}


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # merge defaults
        merged = dict(DEFAULT_CONFIG)
        merged.update(data)
        if "gdrive" not in merged:
            merged["gdrive"] = dict(DEFAULT_CONFIG["gdrive"])
        else:
            g = dict(DEFAULT_CONFIG["gdrive"])
            g.update(merged["gdrive"])
            merged["gdrive"] = g
        return merged
    except Exception:
        return dict(DEFAULT_CONFIG)


def save_config(cfg: Dict[str, Any]) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_PATH)
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass


def get_backend(cfg: Dict[str, Any] = None):
    if cfg is None:
        cfg = load_config()
    if cfg.get("backend") == "gdrive":
        from .backend.gdrive import GoogleDriveBackend
        return GoogleDriveBackend(
            client_secrets_path=cfg.get("gdrive", {}).get("client_secrets_path"),
        )
    from .backend.local import LocalBackend
    return LocalBackend(cfg.get("local_base_dir", os.path.expanduser("~/.local/share/cardsync/drive")))