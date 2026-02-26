# GeoLoop

Styring av vannbåren varme i utendørs bakke (snøsmelting/is-forebygging) via Raspberry Pi, med prediktiv oppstart basert på værdata.

## Systemarkitektur

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Værtjeneste │────▶│              │────▶│  Relékort    │
│  (api.met.no)│     │  Raspberry   │     │  (GPIO)      │
└─────────────┘     │  Pi          │     └──────┬───────┘
                     │              │            │
┌─────────────┐     │  - Styrings- │     ┌──────▼───────┐
│  Temp-       │────▶│    logikk   │     │  Varmepumpe  │
│  sensorer    │     │  - Web UI   │     │              │
└─────────────┘     └──────────────┘     └──────────────┘
```

## Hurtigstart

```bash
# Klon og installer
git clone <repo-url> GeoLoop
cd GeoLoop
sudo bash scripts/install.sh

# Rediger konfigurasjon
nano config.yaml

# Start
sudo systemctl start geoloop

# Sjekk at det kjører
curl http://localhost:8000/api/status
```

Se [docs/oppsett-guide.md](docs/oppsett-guide.md) for fullstendig steg-for-steg-guide med maskinvareoppsett.

## Prosjektstruktur

```
GeoLoop/
├── pyproject.toml            # Avhengigheter og prosjektmetadata
├── config.example.yaml       # Eksempelkonfigurasjon
├── scripts/
│   └── install.sh            # Installer som systemd-tjeneste på RPi
├── geoloop/
│   ├── main.py               # Oppstart, scheduler, livsløp
│   ├── config.py             # Konfig-lasting fra YAML
│   ├── weather/
│   │   └── met_client.py     # api.met.no-klient
│   ├── sensors/
│   │   └── base.py           # Abstrakt sensorgrensesnitt
│   ├── controller/
│   │   └── base.py           # Abstrakt styringsgrensesnitt
│   ├── db/
│   │   └── store.py          # SQLite-logging
│   └── web/
│       └── app.py            # FastAPI med JSON-API
├── tests/
│   ├── test_met_client.py
│   └── test_store.py
└── docs/
    └── oppsett-guide.md      # Maskinvare- og installasjonsguide
```

## API-endepunkter

| Endepunkt | Beskrivelse |
|-----------|-------------|
| `GET /api/status` | Gjeldende tilstand (vær, sensorer, pumpe) |
| `GET /api/weather` | Siste værdata + 24-timers prognose |
| `GET /api/log?limit=50` | Historikk fra databasen |

## Komponenter

### Styringslogikk (kjernen)
- **Beslutningsmotor**: Når skal varmen på/av?
- **Prediktiv modell**: Start oppvarming *før* det blir glatt, basert på treghet i systemet
- **Moduser**: Auto (værbasert), manuell på/av, tidsplan

### Maskinvareintegrasjon (RPi)
- GPIO-styring av relé for varmepumpe av/på
- Temperatursensorer (DS18B20 via 1-Wire)
- Eventuelt fuktsensor for bakken

### Værdataintegrasjon
- **api.met.no** (Yr) — gratis, norsk, god dekning
- Henter: temperatur, nedbør, nedbørstype, vindforhold
- Predikerer isfare basert på kombinasjon av faktorer

## Teknisk stack

| Komponent | Valg | Begrunnelse |
|-----------|------|-------------|
| Språk | Python >=3.11 | Naturlig for RPi, GPIO, rask prototyping |
| Web-rammeverk | FastAPI + uvicorn | Asynkront, lett å kjøre på RPi |
| Værtjeneste | api.met.no | Gratis, norsk, godt dokumentert |
| HTTP-klient | httpx | Asynkron, moderne |
| Tempsensorer | DS18B20 (1-Wire) | Billig, vanntett variant finnes, enkel på RPi |
| Relé | Relékort via GPIO | Enklest, avhenger av strømbehov |
| Database | SQLite | Lokal logging uten ekstra infra |
| Scheduler | APScheduler | Periodisk værhenting |
| Prosesskjøring | systemd | Standard på RPi OS |

## Utvikling

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

## Status

Se [TODO-avklaringer.md](TODO-avklaringer.md) for åpne spørsmål om maskinvare og anlegg.
