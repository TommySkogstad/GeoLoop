FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY geoloop/ ./geoloop/

RUN pip install --no-cache-dir .

CMD ["python", "-c", "from geoloop.main import run; run()"]
