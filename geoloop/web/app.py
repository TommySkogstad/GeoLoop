from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

if TYPE_CHECKING:
    from geoloop.config import AppConfig
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
_config: AppConfig | None = None


def configure(
    met_client: MetClient,
    store: Store,
    lat: float,
    lon: float,
    sensors: dict[str, TemperatureSensor] | None = None,
    controller: HeatingController | None = None,
    config: AppConfig | None = None,
) -> None:
    """Sett opp delte avhengigheter for ruter."""
    global _met_client, _store, _lat, _lon, _sensors, _controller, _config
    _met_client = met_client
    _store = store
    _lat = lat
    _lon = lon
    _sensors = sensors or {}
    _controller = controller
    _config = config


@app.get("/")
async def index() -> FileResponse:
    """Server dashboard."""
    return FileResponse(_STATIC_DIR / "index.html")


@app.get("/info")
async def info_page() -> FileResponse:
    """Server informasjonsside."""
    return FileResponse(_STATIC_DIR / "info.html")


@app.get("/api/system")
async def system_info() -> dict:
    """Systeminformasjon og konfigurasjon."""
    info: dict = {
        "version": "0.1.0",
        "location": {"lat": _lat, "lon": _lon},
    }

    if _config:
        info["weather"] = {
            "poll_interval_minutes": _config.weather.poll_interval_minutes,
        }
        info["web"] = {
            "host": _config.web.host,
            "port": _config.web.port,
        }
        if _config.ground_loop:
            gl = _config.ground_loop
            inner_d = gl.pipe_outer_mm - 2 * gl.pipe_wall_mm
            volume = (3.14159 * (inner_d / 2000) ** 2) * gl.total_length_m * 1000
            info["ground_loop"] = {
                "loops": gl.loops,
                "total_length_m": gl.total_length_m,
                "pipe_outer_mm": gl.pipe_outer_mm,
                "pipe_wall_mm": gl.pipe_wall_mm,
                "volume_liters": round(volume),
            }
        if _config.tank:
            info["tank"] = {"volume_liters": _config.tank.volume_liters}
        if _config.relays:
            info["relays"] = {
                name: {"gpio_pin": r.gpio_pin, "active_high": r.active_high}
                for name, r in _config.relays.items()
            }
        if _config.sensors:
            info["sensors"] = {
                name: {"id": s.id} for name, s in _config.sensors.items()
            }

    # Database stats
    if _store:
        info["database"] = {
            "sensor_readings": len(_store.get_sensor_log(limit=999999)),
            "weather_readings": len(_store.get_weather_log(limit=999999)),
            "events": len(_store.get_events(limit=999999)),
        }

    return info


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


@app.get("/api/history")
async def history(hours: int = 24) -> dict:
    """Sensorhistorikk og VP-perioder for tidsserie-graf."""
    if not _store:
        return {"error": "Database ikke konfigurert"}

    heating_on = False
    if _controller:
        heating_on = await _controller.is_on()

    return {
        "sensors": _store.get_sensor_history(hours=hours),
        "heating_periods": _store.get_heating_periods(hours=hours),
        "heating_on": heating_on,
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
