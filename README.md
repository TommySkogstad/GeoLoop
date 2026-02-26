# GeoLoop

Styring av vannbåren varme i utendørs bakke (snøsmelting/is-forebygging) via Raspberry Pi, med prediktiv oppstart basert på værdata.

## Systemarkitektur

```
┌─────────────┐     ┌────────────────────────┐     ┌──────────────────┐
│  Værtjeneste │────▶│  Raspberry Pi 3B+      │     │  RPi Relay Board │
│  (api.met.no)│     │                        │────▶│  (3 kanaler)     │
└─────────────┘     │  + Open-Smart GPIO     │     │                  │
                     │    Expansion           │     │  K1: VP ON/OFF   │
┌─────────────┐     │                        │     │  K2: Sirk.pumpe  │
│  Temp-       │────▶│  - Styringslogikk      │     │  K3: Ledig       │
│  sensorer    │     │  - Web UI / API        │     └────────┬─────────┘
│  (5 stk)     │     └────────────────────────┘              │
└─────────────┘                                     ┌────────▼─────────┐
                                                    │  Panasonic       │
                                                    │  WH-MXC12G6E5   │
                                                    │  (klemme 17/18)  │
                                                    └──────────────────┘
```

## Maskinvare

| Komponent | Modell | Rolle |
|-----------|--------|-------|
| Styringsenhet | Raspberry Pi 3B+ | Kjører GeoLoop-programvaren |
| Relékort | RPi Relay Board (3 kanaler, HAT) | Styrer VP og sirkulasjonspumpe |
| GPIO-utvidelse | Open-Smart GPIO Expansion Board | Ekstra pinner til sensorer |
| Varmepumpe | Panasonic WH-MXC12G6E5 (Aquarea G-gen) | Luft-vann, hovedvarmekilden |
| Kolber | 10 kW elektriske, 10 L tank | Tilleggsvarme på VP inngang (ingen styring ennå) |
| Sirkulasjonspumpe | Ekstern + intern (følger VP) | Sirkulerer varme i bakkeløyfen |
| Bakkeløyfe | 8 sløyfer, 900 m totalt (20/16 mm) | ~181 liter vannvolum |
| Buffertank | 200 liter | Tankføler på VP klemme 15/16 |

### Temperatursensorer (5 målepunkter)

| # | Plassering | Formål |
|---|------------|--------|
| T1 | Inn til varmesløyfe (bakke) | Turtemperatur til bakken |
| T2 | Ut av varmesløyfe (bakke) | Returtemperatur fra bakken (delta-T) |
| T3 | Inn til varmepumpe | Returvann til VP |
| T4 | Ut av varmepumpe | Turvann fra VP |
| T5 | Vanntank (200 L) | Buffertemperatur (VP klemme 15/16) |

### Relétilkoblinger

| Kanal | Funksjon | Tilkobling |
|-------|----------|------------|
| 1 | Varmepumpe ON/OFF | VP klemme 17/18 (potensialfri, erstatter fabrikkjumper) |
| 2 | Ekstern sirkulasjonspumpe | Uavhengig av VP |
| 3 | Ledig | Reservert for fremtidig bruk (kolber) |

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
    ├── oppsett-guide.md                          # Maskinvare- og installasjonsguide
    ├── CZ-TAW1-OI-1.pdf                          # CZ-TAW1 dok (ikke kompatibel)
    └── SM-WHMXC09G3E5_WH-MXC12G6E5.pdf          # VP servicemanual
```

## API-endepunkter

| Endepunkt | Beskrivelse |
|-----------|-------------|
| `GET /api/status` | Gjeldende tilstand (vær, sensorer, releer) |
| `GET /api/weather` | Siste værdata + 24-timers prognose |
| `GET /api/log?limit=50` | Historikk fra databasen |

## Komponenter

### Styringslogikk (kjernen)
- **Beslutningsmotor**: Når skal varmen på/av?
- **Prediktiv modell**: Start oppvarming *før* det blir glatt, basert på treghet i systemet
- **Moduser**: Auto (værbasert), manuell på/av, tidsplan

### Maskinvareintegrasjon (RPi)
- GPIO-styring av 3 relékanaler via RPi Relay Board (HAT)
- 5 temperatursensorer (tur/retur bakke, tur/retur VP, vanntank)
- Ekstern kontrollkabel til VP klemme 17/18 (potensialfri ON/OFF)

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
| Relé | RPi Relay Board (3-kanals HAT) | Sitter direkte på RPi, 3 uavhengige kanaler |
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

Se [TODO-avklaringer.md](TODO-avklaringer.md) for åpne spørsmål og full maskinvareoversikt.
