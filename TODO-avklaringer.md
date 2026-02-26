# Avklaringer

Spørsmål som må besvares før vi kan lage detaljert design og begynne å kode.

## A. Eksisterende anlegg (avklart)

- [x] **Varmepumpe**: Panasonic WH-MXC12G6E5 (Aquarea G-generasjon, luft-vann monobloc). Har innebygd termostat/styringssystem.
- [x] **Ekstern kontrollkabel**: 2-leder potensialfri fra **klemme 17/18** på VP. Fabrikkjumper mellom 17/18 = VP alltid på. **Hard ON/OFF** — lukket krets = VP på, åpen = VP helt av.
- [x] **Romtermostat**: Klemme 9 (L), 10 (N), 12 (Heat) — ekstern romtermostat for varmebehov-signal. Klemme 11 er kjøling (ikke aktuelt for snøsmelting).
- [x] **Sirkulasjonspumpe**: Intern pumpe følger VP. I tillegg en ekstern sirkulasjonspumpe som må styres separat via relé.
- [x] **Kolber**: 10 kW elektriske varmekolber på inngangskretsen til VP, med egen 10 L tank. Ingen styring i dag. Mulig fremtidig tillegg.
- [x] **CZ-TAW1**: Ikke kompatibel med G-generasjon (krever H-gen+ og CN-CNT-kontakt som ikke finnes på denne modellen).
- [x] **HeishaMon**: Ikke kompatibel med G-generasjon. G-serien bruker annen protokoll (960 baud, invertert signal) enn H/J/K/L (9600 baud). Alternativ: aquarea_esphome (ubekreftet for G-serie).

### Systemtopologi

Buffertanken (200 L, udelt) er sentral node. To separate kretser:

```
     VP-krets                                  Bakkesløyfe-krets

┌─────────────────┐                     ┌─────────────────────────┐
│   Varmepumpe    │                     │   Bakkeløyfe            │
│  WH-MXC12G6E5  │                     │   8 sløyfer, 900 m      │
└──┬──────────▲───┘                     └──┬──────────────▲───────┘
   │          │                            │              │
 T4(ut)       │                        T1(inn)         T2(ut)
   │     ┌────┴────────┐                  │              │
   │     │ Kolbetank   │                  │              │
   │     │ 10 L        │                  │              │
   │     │ 10 kW kolber│                  │              │
   │     └────▲────────┘                  │              │
   │          │                            │              │
   │       T3(inn)                         │              │
   │          │                            │              │
   ▼          │                            ▼              │
┌─────────────┴────────────────────────────┴──────────────┴───────┐
│                    Buffertank 200 L (T5)                         │
│                    (udelt felles volum, føler kl. 15/16)         │
└─────────────────────────────────────────────────────────────────┘
```

### Temperatursensorer — 5 målepunkter

Rørfølere finnes, type ukjent — må sjekkes fysisk.

| # | Plassering | Krets | Formål |
|---|------------|-------|--------|
| T1 | Tank → bakkeløyfe | Bakkesløyfe | Turtemperatur til bakken |
| T2 | Bakkeløyfe → tank | Bakkesløyfe | Returtemperatur fra bakken (delta-T → effekt) |
| T3 | Tank → varmepumpe | VP | Returvann til VP (via kolbetank) |
| T4 | Varmepumpe → tank | VP | Turvann fra VP |
| T5 | Buffertank (200 L) | Felles | Buffertemperatur (VP klemme 15/16) |

### VP klemmerekke (fra servicemanual)

| Klemme | Funksjon | Kabeltype |
|--------|----------|-----------|
| 1-2 | Toveisventil (lukk/åpne) | Two-way Valve Cable |
| 3-5 | Treveisventil (N/lukk/åpne) | Three-way Valve Cable |
| 6 | Tilleggsvarme (N) | Booster Heater Cord |
| 9 (L), 10 (N) | Romtermostat strøm | Room Thermostat Cable |
| 11 | Kjøling | Ikke aktuelt |
| 12 | Varme (Heat) | Room Thermostat Cable |
| 13 | Varme | Tank OLP Cable |
| **15-16** | **Tankføler** | **Tank Sensor Cable (200L tank)** |
| **17-18** | **Ekstern kontroller (ON/OFF)** | **External Controller Cable** |
| 19-20 | Solventil | Solar Three-way Valve Cable |
| 21-23 | Solpumpe | Solar Pump Station Cable |

## B. Maskinvare (avklart)

- [x] **RPi**: Raspberry Pi 3B+
- [x] **Relékort**: RPi Relay Board — 3 kanaler (HAT-format)
- [x] **GPIO-utvidelse**: Open-Smart GPIO Expansion Board — ekstra pinner til sensorer
- [x] **Temperatursensorer**: DS18B20 (1-Wire), hardkoblet, 5 stk

### Planlagt relébruk

| Kanal | Funksjon | Tilkobling |
|-------|----------|------------|
| 1 | Varmepumpe ON/OFF | Klemme 17/18 (erstatter fabrikkjumper) |
| 2 | Ekstern sirkulasjonspumpe | Uavhengig av VP |
| 3 | Ledig / kolber (fremtidig) | Reservert for utvidelse |

## C. Infrastruktur på stedet (avklart)

- [x] **Strøm**: Ja, tilgjengelig
- [x] **Nettverk**: Både Ethernet og WiFi tilgjengelig
- [x] **Plassering**: Innendørs (ingen kapsling nødvendig)

## C.5 Bakkeløyfe (avklart)

- [x] **Antall sløyfer**: 8
- [x] **Total rørlengde**: 900 m (~112 m per sløyfe)
- [x] **Rørtype**: 20 mm ytre diameter, 2 mm veggtykkelse → 16 mm indre diameter
- [x] **Beregnet vannvolum sløyfe**: ~181 liter (π × 0.008² × 900 = 0.181 m³)
- [x] **Buffertank**: 200 liter (tankføler på VP klemme 15/16)
- [x] **Kolbetank**: 10 liter (på inngangskretsen til VP, med 10 kW varmekolber)
- [x] **Internrør**: ~30 liter (rør mellom komponenter internt i systemet)
- [x] **Totalt vannvolum**: ~421 liter (181 L sløyfe + 200 L buffer + 10 L kolbetank + ~30 L internrør)
- [x] **Areal**: ~90 m² dekket av bakkeløyfen
- [x] **Legging**: Rør i sand, 5 cm under overflaten, asfalt over

## D. Prediktiv logikk — gjenstår

- [x] **Treghet i systemet**: Estimert ~24 timer fra oppstart til full effekt. Værprediksjonen må se minst 24 timer frem i tid.
- [x] **Temperaturgrenser**: -5 °C til +5 °C er faresonen — rundt 0 °C er kritisk
- [x] **Prioritet**: Sikkerhet mot is — hellere kjøre for mye enn å risikere glatt

## E. Funksjonelle ønsker (avklart)

- [x] **Fjernstyring**: Ja — skal kunne styres utenfra
- [x] **Varsling**: Ja — varsling når noe er galt (feil, sensorbortfall, VP stopp etc.)
- [x] **Logging**: Ja — historikk som kan sjekkes i ettertid
- [x] **Grafing**: Temperatur over tid — visuelt dashboard
- [x] **Statistikk**: Driftsstatistikk og forbruksoversikt

## F. Temperaturfølere (avklart)

- [x] **Type**: DS18B20 (1-Wire digital)
- [x] **Tilkobling**: Hardkoblet
- [x] **Antall**: 5 stk (T1–T5)
- [x] **GPIO**: Alle på GPIO4 (1-Wire-buss), ingen ADC nødvendig

## Referansedokumentasjon

- [docs/CZ-TAW1-OI-1.pdf](docs/CZ-TAW1-OI-1.pdf) — Panasonic CZ-TAW1 nettverksadapter (ikke kompatibel med G-gen)
- [docs/SM-WHMXC09G3E5_WH-MXC12G6E5.pdf](docs/SM-WHMXC09G3E5_WH-MXC12G6E5.pdf) — Servicemanual for varmepumpen
