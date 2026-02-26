from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

if TYPE_CHECKING:
    from geoloop.db.store import Store
    from geoloop.weather.met_client import MetClient, WeatherForecast

app = FastAPI(title="GeoLoop", version="0.1.0")

_met_client: MetClient | None = None
_store: Store | None = None
_lat: float = 0.0
_lon: float = 0.0


def configure(
    met_client: MetClient, store: Store, lat: float, lon: float
) -> None:
    """Sett opp delte avhengigheter for ruter."""
    global _met_client, _store, _lat, _lon
    _met_client = met_client
    _store = store
    _lat = lat
    _lon = lon


@app.get("/api/status")
async def status() -> dict:
    weather: WeatherForecast | None = None
    if _met_client:
        weather = await _met_client.fetch_forecast(_lat, _lon)

    current = None
    if weather:
        c = weather.current
        current = {
            "air_temperature": c.air_temperature,
            "precipitation_amount": c.precipitation_amount,
            "relative_humidity": c.relative_humidity,
            "wind_speed": c.wind_speed,
        }

    return {
        "weather": current,
        "heating": None,  # Fylles inn når controller er implementert
    }


@app.get("/api/weather")
async def weather() -> dict:
    if not _met_client:
        return {"error": "Værklient ikke konfigurert"}

    forecast = await _met_client.fetch_forecast(_lat, _lon)
    current = forecast.current

    return {
        "current": {
            "time": current.time.isoformat(),
            "air_temperature": current.air_temperature,
            "precipitation_amount": current.precipitation_amount,
            "relative_humidity": current.relative_humidity,
            "wind_speed": current.wind_speed,
        },
        "forecast": [
            {
                "time": s.time.isoformat(),
                "air_temperature": s.air_temperature,
                "precipitation_amount": s.precipitation_amount,
                "relative_humidity": s.relative_humidity,
                "wind_speed": s.wind_speed,
            }
            for s in forecast.timeseries[:24]
        ],
    }


@app.get("/api/log")
async def log(limit: int = 50) -> dict:
    if not _store:
        return {"error": "Database ikke konfigurert"}

    return {
        "weather": _store.get_weather_log(limit=limit),
        "sensors": _store.get_sensor_log(limit=limit),
        "events": _store.get_events(limit=limit),
    }
