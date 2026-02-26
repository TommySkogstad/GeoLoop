# GeoLoop

Styring av vannbaren varme i utendors bakke (snosmelting/is-forebygging) via Raspberry Pi, med prediktiv oppstart basert pa vaerdata.

## Systemarkitektur

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Vaertjeneste│────▶│              │────▶│  Rele-kort   │
│  (api.met.no)│     │  Raspberry   │     │  (GPIO)      │
└─────────────┘     │  Pi          │     └──────┬───────┘
                     │              │            │
┌─────────────┐     │  - Styrings- │     ┌──────▼───────┐
│  Temp-       │────▶│    logikk   │     │  Varmepumpe  │
│  sensorer    │     │  - Web UI   │     │              │
└─────────────┘     └──────────────┘     └──────────────┘
```

## Komponenter

### 1. Styringslogikk (kjernen)
- **Beslutningsmotor**: Nar skal varmen pa/av?
- **Prediktiv modell**: Start oppvarming *for* det blir glatt, basert pa treghet i systemet
- **Moduser**: Auto (vaerbasert), Manuell pa/av, Tidsplan

### 2. Maskinvare-integrasjon (RPi)
- GPIO-styring av rele for varmepumpe pa/av
- Temperatursensorer (DS18B20 via 1-Wire)
- Eventuelt fuktsensor for bakken

### 3. Vaerdata-integrasjon
- **api.met.no** (Yr) — gratis, norsk, god dekning
- Henter: temperatur, nedbor, nedborstype, vindforhold
- Predikterer isfare basert pa kombinasjon av faktorer

### 4. Brukergrensesnitt
- Enkel web-UI pa RPi (dashboard, innstillinger, logg)
- Eventuelt mobilvarslinger ved oppstart/feil

## Teknisk stack

| Komponent | Valg | Begrunnelse |
|-----------|------|-------------|
| Sprak | Python 3 | Naturlig for RPi, GPIO, rask prototyping |
| Vaertjeneste | api.met.no | Gratis, norsk, godt dokumentert |
| Temp-sensorer | DS18B20 (1-Wire) | Billig, vanntett variant finnes, enkel pa RPi |
| Rele | Rele-HAT for RPi | Enklest, avhenger av strombehov |
| Database | SQLite | Lokal logging uten ekstra infra |
| Web-UI | FastAPI + enkel frontend | Lett a kjore pa RPi |
| Prosesskjoring | systemd | Standard pa RPi OS |
