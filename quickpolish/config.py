import json
from pathlib import Path

DEFAULTS = {
    "hotkey": "alt+space",
    "model": "gpt-4o",
    "openai_api_key": None,
}


class Config:
    def __init__(self, config_dir: Path = None):
        self._dir = config_dir or Path.home() / ".quickpolish"
        self._path = self._dir / "config.json"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            with open(self._path) as f:
                return {**DEFAULTS, **json.load(f)}
        return dict(DEFAULTS)

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value):
        self._data[key] = value
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def has_api_key(self) -> bool:
        key = self._data.get("openai_api_key")
        return bool(key and key.strip())
