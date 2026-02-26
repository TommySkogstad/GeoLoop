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

## Komponenter

### 1. Styringslogikk (kjernen)
- **Beslutningsmotor**: Når skal varmen på/av?
- **Prediktiv modell**: Start oppvarming *før* det blir glatt, basert på treghet i systemet
- **Moduser**: Auto (værbasert), manuell på/av, tidsplan

### 2. Maskinvareintegrasjon (RPi)
- GPIO-styring av relé for varmepumpe på/av
- Temperatursensorer (DS18B20 via 1-Wire)
- Eventuelt fuktsensor for bakken

### 3. Værdataintegrasjon
- **api.met.no** (Yr) — gratis, norsk, god dekning
- Henter: temperatur, nedbør, nedbørstype, vindforhold
- Predikerer isfare basert på kombinasjon av faktorer

### 4. Brukergrensesnitt
- Enkel web-UI på RPi (dashboard, innstillinger, logg)
- Eventuelt mobilvarslinger ved oppstart/feil

## Teknisk stack

| Komponent | Valg | Begrunnelse |
|-----------|------|-------------|
| Språk | Python 3 | Naturlig for RPi, GPIO, rask prototyping |
| Værtjeneste | api.met.no | Gratis, norsk, godt dokumentert |
| Tempsensorer | DS18B20 (1-Wire) | Billig, vanntett variant finnes, enkel på RPi |
| Relé | Relé-HAT for RPi | Enklest, avhenger av strømbehov |
| Database | SQLite | Lokal logging uten ekstra infra |
| Web-UI | FastAPI + enkel frontend | Lett å kjøre på RPi |
| Prosesskjøring | systemd | Standard på RPi OS |
