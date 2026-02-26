from __future__ import annotations

import asyncio
import logging

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from geoloop.config import load_config
from geoloop.db.store import Store
from geoloop.weather.met_client import MetClient
from geoloop.web.app import app, configure

logger = logging.getLogger("geoloop")


async def _poll_weather(
    met_client: MetClient, store: Store, lat: float, lon: float
) -> None:
    """Hent værdata og logg til database."""
    try:
        forecast = await met_client.fetch_forecast(lat, lon)
        c = forecast.current
        store.log_weather(
            temperature=c.air_temperature,
            precipitation=c.precipitation_amount,
            humidity=c.relative_humidity,
            wind_speed=c.wind_speed,
        )
        logger.info("Værdata logget: %.1f°C", c.air_temperature or 0)
    except Exception:
        logger.exception("Feil ved henting av værdata")
        store.log_event("error", "Feil ved henting av værdata")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    cfg = load_config()
    store = Store(cfg.database.path)
    met_client = MetClient(cfg.weather.user_agent)

    configure(
        met_client=met_client,
        store=store,
        lat=cfg.location.lat,
        lon=cfg.location.lon,
    )

    store.log_event("startup", "GeoLoop startet")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _poll_weather,
        "interval",
        minutes=cfg.weather.poll_interval_minutes,
        args=[met_client, store, cfg.location.lat, cfg.location.lon],
    )
    scheduler.start()

    # Hent værdata umiddelbart ved oppstart
    await _poll_weather(
        met_client, store, cfg.location.lat, cfg.location.lon
    )

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=cfg.web.host,
            port=cfg.web.port,
            log_level="info",
        )
    )

    try:
        await server.serve()
    finally:
        scheduler.shutdown()
        store.close()


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
