from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class LocationConfig:
    lat: float
    lon: float


@dataclass
class WeatherConfig:
    user_agent: str
    poll_interval_minutes: int = 30


@dataclass
class DatabaseConfig:
    path: str = "geoloop.db"


@dataclass
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class AppConfig:
    location: LocationConfig
    weather: WeatherConfig
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    web: WebConfig = field(default_factory=WebConfig)


def load_config(path: Path | None = None) -> AppConfig:
    """Last konfigurasjon fra YAML-fil.

    Prøver ``config.yaml`` først, deretter ``config.example.yaml``.
    """
    if path is None:
        root = Path.cwd()
        candidates = [root / "config.yaml", root / "config.example.yaml"]
        for candidate in candidates:
            if candidate.exists():
                path = candidate
                break
        if path is None:
            raise FileNotFoundError(
                "Fant verken config.yaml eller config.example.yaml"
            )

    raw = yaml.safe_load(path.read_text())

    return AppConfig(
        location=LocationConfig(**raw["location"]),
        weather=WeatherConfig(**raw["weather"]),
        database=DatabaseConfig(**raw.get("database", {})),
        web=WebConfig(**raw.get("web", {})),
    )
