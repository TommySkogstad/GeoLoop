from datetime import datetime, timezone

from geoloop.db.store import Store


class TestStore:
    def setup_method(self):
        self.store = Store(":memory:")

    def teardown_method(self):
        self.store.close()

    def test_should_insert_weather_log_when_called(self):
        self.store.log_weather(temperature=-3.0, precipitation=0.5)
        rows = self.store.get_weather_log()
        assert len(rows) == 1
        assert rows[0]["temperature"] == -3.0
        assert rows[0]["precipitation"] == 0.5

    def test_should_store_timestamp_when_provided(self):
        ts = datetime(2025, 1, 15, 12, 0, tzinfo=timezone.utc)
        self.store.log_weather(temperature=1.0, timestamp=ts)
        rows = self.store.get_weather_log()
        assert rows[0]["timestamp"] == ts.isoformat()

    def test_should_insert_sensor_log_when_called(self):
        self.store.log_sensor("temp_bakke_1", 5.2)
        rows = self.store.get_sensor_log()
        assert len(rows) == 1
        assert rows[0]["sensor_id"] == "temp_bakke_1"
        assert rows[0]["value"] == 5.2

    def test_should_filter_sensor_log_when_sensor_id_provided(self):
        self.store.log_sensor("sensor_a", 1.0)
        self.store.log_sensor("sensor_b", 2.0)
        rows = self.store.get_sensor_log(sensor_id="sensor_a")
        assert len(rows) == 1
        assert rows[0]["sensor_id"] == "sensor_a"

    def test_should_insert_event_when_called(self):
        self.store.log_event("startup", "System startet")
        rows = self.store.get_events()
        assert len(rows) == 1
        assert rows[0]["event_type"] == "startup"
        assert rows[0]["message"] == "System startet"

    def test_should_respect_limit_when_querying_weather(self):
        for i in range(10):
            self.store.log_weather(temperature=float(i))
        rows = self.store.get_weather_log(limit=3)
        assert len(rows) == 3

    def test_should_return_newest_first_when_querying(self):
        self.store.log_weather(temperature=1.0)
        self.store.log_weather(temperature=2.0)
        rows = self.store.get_weather_log()
        assert rows[0]["temperature"] == 2.0
