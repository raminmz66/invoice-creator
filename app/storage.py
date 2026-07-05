"""JSON file persistence for settings and application state."""

from __future__ import annotations

import json
from pathlib import Path

from app.models import AppState, Settings

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SETTINGS_PATH = DATA_DIR / "settings.json"
STATE_PATH = DATA_DIR / "state.json"


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def load_settings() -> Settings | None:
    """Load settings from disk, or return None if the file is missing."""
    raw = _read_json(SETTINGS_PATH)
    return Settings.model_validate(raw) if raw else None


def save_settings(settings: Settings) -> None:
    """Persist settings to disk using JSON field aliases."""
    _write_json(SETTINGS_PATH, settings.model_dump(by_alias=True))


def load_state() -> AppState | None:
    """Load application state from disk, or return None if the file is missing."""
    raw = _read_json(STATE_PATH)
    return AppState.model_validate(raw) if raw else None


def save_state(state: AppState) -> None:
    """Persist application state to disk."""
    _write_json(STATE_PATH, state.model_dump(mode="json"))
