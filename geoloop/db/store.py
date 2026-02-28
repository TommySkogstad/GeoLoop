from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


class Store:
    """SQLite-basert logging for GeoLoop."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(
            str(path),
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        cur = self._conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS weather_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT    NOT NULL,
                temperature    REAL,
                precipitation  REAL,
                humidity       REAL,
                wind_speed     REAL
            );

            CREATE TABLE IF NOT EXISTS sensor_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT    NOT NULL,
                sensor_id TEXT    NOT NULL,
                value     REAL
            );

            CREATE TABLE IF NOT EXISTS system_events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT    NOT NULL,
                event_type TEXT    NOT NULL,
                message    TEXT
            );
        """)
        self._conn.commit()

    def log_weather(
        self,
        *,
        temperature: float | None = None,
        precipitation: float | None = None,
        humidity: float | None = None,
        wind_speed: float | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        ts = (timestamp or datetime.now(timezone.utc)).isoformat()
        self._conn.execute(
            "INSERT INTO weather_log (timestamp, temperature, precipitation, humidity, wind_speed) "
            "VALUES (?, ?, ?, ?, ?)",
            (ts, temperature, precipitation, humidity, wind_speed),
        )
        self._conn.commit()

    def log_sensor(
        self,
        sensor_id: str,
        value: float,
        *,
        timestamp: datetime | None = None,
    ) -> None:
        ts = (timestamp or datetime.now(timezone.utc)).isoformat()
        self._conn.execute(
            "INSERT INTO sensor_log (timestamp, sensor_id, value) VALUES (?, ?, ?)",
            (ts, sensor_id, value),
        )
        self._conn.commit()

    def log_event(
        self,
        event_type: str,
        message: str = "",
        *,
        timestamp: datetime | None = None,
    ) -> None:
        ts = (timestamp or datetime.now(timezone.utc)).isoformat()
        self._conn.execute(
            "INSERT INTO system_events (timestamp, event_type, message) VALUES (?, ?, ?)",
            (ts, event_type, message),
        )
        self._conn.commit()

    def get_weather_log(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM weather_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]

    def get_sensor_log(
        self, sensor_id: str | None = None, limit: int = 100
    ) -> list[dict]:
        if sensor_id:
            rows = self._conn.execute(
                "SELECT * FROM sensor_log WHERE sensor_id = ? ORDER BY id DESC LIMIT ?",
                (sensor_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM sensor_log ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_events(self, limit: int = 100) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM system_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_sensor_history(self, hours: int = 24) -> list[dict]:
        """Hent sensordata pivotert per tidsstempel for de siste N timer."""
        since = (
            datetime.now(timezone.utc)
            - timedelta(hours=hours)
        ).isoformat()
        rows = self._conn.execute(
            """
            SELECT timestamp,
                   MAX(CASE WHEN sensor_id = 'loop_inlet'  THEN value END) AS loop_inlet,
                   MAX(CASE WHEN sensor_id = 'loop_outlet' THEN value END) AS loop_outlet,
                   MAX(CASE WHEN sensor_id = 'hp_inlet'    THEN value END) AS hp_inlet,
                   MAX(CASE WHEN sensor_id = 'hp_outlet'   THEN value END) AS hp_outlet,
                   MAX(CASE WHEN sensor_id = 'tank'        THEN value END) AS tank
            FROM sensor_log
            WHERE timestamp >= ?
            GROUP BY timestamp
            ORDER BY timestamp ASC
            """,
            (since,),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_heating_periods(self, hours: int = 24) -> list[dict]:
        """Hent VP av/på-hendelser for de siste N timer."""
        since = (
            datetime.now(timezone.utc)
            - timedelta(hours=hours)
        ).isoformat()
        rows = self._conn.execute(
            """
            SELECT timestamp, event_type
            FROM system_events
            WHERE event_type IN ('heating_on', 'heating_off', 'manual_on', 'manual_off')
              AND timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (since,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self._conn.close()
