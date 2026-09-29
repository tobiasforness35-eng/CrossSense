from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

APP_DIR = Path.home() / "AppData" / "Local" / "CrossSense"
SETTINGS_PATH = APP_DIR / "settings.json"


@dataclass
class Settings:
    inner_deadzone_percent: float = 6.0
    outer_saturation_percent: float = 83.0
    # v8 default is pure Steam Cross 6-83. Add 1.0–1.5 only if flip cancel feels weak.
    forward_boost_percent: float = 0.0
    auto_start: bool = False
    minimize_on_start: bool = False


def load_settings() -> Settings:
    try:
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            return Settings(
                inner_deadzone_percent=float(data.get("inner_deadzone_percent", 6.0)),
                outer_saturation_percent=float(data.get("outer_saturation_percent", 83.0)),
                forward_boost_percent=float(data.get("forward_boost_percent", 0.0)),
                auto_start=bool(data.get("auto_start", False)),
                minimize_on_start=bool(data.get("minimize_on_start", False)),
            )
    except Exception:
        pass
    return Settings()


def save_settings(settings: Settings) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
