from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

if TYPE_CHECKING:
    from geoloop.controller.base import HeatingController
    from geoloop.db.store import Store
    from geoloop.sensors.base import TemperatureSensor
    from geoloop.weather.met_client import MetClient, WeatherForecast

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="GeoLoop", version="0.1.0")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

_met_client: MetClient | None = None
_store: Store | None = None
_lat: float = 0.0
_lon: float = 0.0
_sensors: dict[str, TemperatureSensor] = {}
_controller: HeatingController | None = None


def configure(
    met_client: MetClient,
    store: Store,
    lat: float,
    lon: float,
    sensors: dict[str, TemperatureSensor] | None = None,
    controller: HeatingController | None = None,
) -> None:
    """Sett opp delte avhengigheter for ruter."""
    global _met_client, _store, _lat, _lon, _sensors, _controller
    _met_client = met_client
    _store = store
    _lat = lat
    _lon = lon
    _sensors = sensors or {}
    _controller = controller


@app.get("/")
async def index() -> FileResponse:
    """Server dashboard."""
    return FileResponse(_STATIC_DIR / "index.html")


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

    heating = None
    if _controller:
        heating = {"on": await _controller.is_on()}

    sensor_data = {}
    for name, sensor in _sensors.items():
        sensor_data[name] = await sensor.read()

    return {
        "weather": current,
        "heating": heating,
        "sensors": sensor_data,
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


@app.get("/api/sensors")
async def sensors() -> dict:
    """Les alle sensorer."""
    data = {}
    for name, sensor in _sensors.items():
        data[name] = await sensor.read()
    return {"sensors": data}


@app.post("/api/heating/on")
async def heating_on() -> dict:
    """Manuell overstyring: slå på varme."""
    if not _controller:
        return {"error": "Controller ikke konfigurert"}

    await _controller.turn_on()
    if _store:
        _store.log_event("manual_on", "Manuell overstyring: varme PÅ")
    logger.info("Manuell overstyring: varme PÅ")
    return {"heating": {"on": True}}


@app.post("/api/heating/off")
async def heating_off() -> dict:
    """Manuell overstyring: slå av varme."""
    if not _controller:
        return {"error": "Controller ikke konfigurert"}

    await _controller.turn_off()
    if _store:
        _store.log_event("manual_off", "Manuell overstyring: varme AV")
    logger.info("Manuell overstyring: varme AV")
    return {"heating": {"on": False}}


@app.get("/api/log")
async def log(limit: int = 50) -> dict:
    if not _store:
        return {"error": "Database ikke konfigurert"}

    return {
        "weather": _store.get_weather_log(limit=limit),
        "sensors": _store.get_sensor_log(limit=limit),
        "events": _store.get_events(limit=limit),
    }
