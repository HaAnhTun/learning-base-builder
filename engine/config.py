"""Load configuration: config.yaml -> config.local.yaml -> environment variables."""
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOKEN_ENV = "UDEMY_ACCESS_TOKEN"
LOCAL_FILE = "config.local.yaml"


def _merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_config(root: Path = ROOT) -> dict:
    cfg = _merge(_read_yaml(root / "config.yaml"), _read_yaml(root / LOCAL_FILE))
    cfg.setdefault("udemy", {})
    if os.environ.get(TOKEN_ENV):
        cfg["udemy"]["access_token"] = os.environ[TOKEN_ENV]
    cfg["root"] = root
    return cfg


def path_of(cfg: dict, key: str) -> Path:
    return cfg["root"] / cfg["paths"][key]


def save_token(token: str, root: Path = ROOT) -> Path:
    """Write access_token into config.local.yaml, keeping every other key."""
    path = root / LOCAL_FILE
    data = _read_yaml(path)
    data.setdefault("udemy", {})["access_token"] = token
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path
