# Avklaringer

Spørsmål som må besvares før vi kan lage detaljert design og begynne å kode.

## A. Eksisterende anlegg (avklart)

- [x] **Varmepumpe**: Panasonic WH-MXC12G6E5 (Aquarea G-generasjon, luft-vann monobloc). Har innebygd termostat/styringssystem.
- [x] **Ekstern kontrollkabel**: 2-leder potensialfri fra **klemme 17/18** på VP. Fabrikkjumper mellom 17/18 = VP alltid på. **Hard ON/OFF** — lukket krets = VP på, åpen = VP helt av.
- [x] **Romtermostat**: Klemme 9 (L), 10 (N), 12 (Heat) — ekstern romtermostat for varmebehov-signal. Klemme 11 er kjøling (ikke aktuelt for snøsmelting).
- [x] **Sirkulasjonspumpe**: Intern pumpe følger VP. I tillegg en ekstern sirkulasjonspumpe som må styres separat via relé.
- [x] **Kolber**: 10 kW elektriske varmekolber finnes, men ingen styring i dag. Mulig fremtidig tillegg.
- [x] **CZ-TAW1**: Ikke kompatibel med G-generasjon (krever H-gen+ og CN-CNT-kontakt som ikke finnes på denne modellen).
- [x] **HeishaMon**: Ikke kompatibel med G-generasjon. G-serien bruker annen protokoll (960 baud, invertert signal) enn H/J/K/L (9600 baud). Alternativ: aquarea_esphome (ubekreftet for G-serie).

### Temperatursensorer — 5 målepunkter

Rørfølere finnes, type ukjent — må sjekkes fysisk.

| # | Plassering | Formål |
|---|------------|--------|
| T1 | Inn til varmesløyfe (bakke) | Turtemperatur til bakken |
| T2 | Ut av varmesløyfe (bakke) | Returtemperatur fra bakken (delta-T → effekt) |
| T3 | Inn til varmepumpe | Returvann til VP |
| T4 | Ut av varmepumpe | Turvann fra VP |
| T5 | Vanntank (200 L) | Buffertemperatur (VP klemme 15/16) |

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
- [x] **Temperatursensorer**: Rørtemperaturfølere (type ukjent) + DS18B20 for ute/bakke

### Planlagt relébruk

| Kanal | Funksjon | Tilkobling |
|-------|----------|------------|
| 1 | Varmepumpe ON/OFF | Klemme 17/18 (erstatter fabrikkjumper) |
| 2 | Ekstern sirkulasjonspumpe | Uavhengig av VP |
| 3 | Ledig / kolber (fremtidig) | Reservert for utvidelse |

## C. Infrastruktur på stedet — gjenstår

- [ ] **Strøm**: Har RPi tilgang til strøm der den skal monteres?
- [ ] **Nettverk**: WiFi eller Ethernet tilgjengelig?
- [ ] **Plassering**: Innendørs (teknisk rom) eller utendørs (kapsling nødvendig)?

## C.5 Bakkeløyfe (avklart)

- [x] **Antall sløyfer**: 8
- [x] **Total rørlengde**: 900 m (~112 m per sløyfe)
- [x] **Rørtype**: 20 mm ytre diameter, 2 mm veggtykkelse → 16 mm indre diameter
- [x] **Beregnet vannvolum sløyfe**: ~181 liter (π × 0.008² × 900 = 0.181 m³)
- [x] **Buffertank**: 200 liter (tankføler på VP klemme 15/16)
- [x] **Totalt vannvolum**: ~381 liter (181 L sløyfe + 200 L tank)
- [ ] **Areal**: Hvor stort areal dekker bakkeløyfen?

## D. Prediktiv logikk — gjenstår

- [ ] **Treghet i systemet**: Tidsforsinkelse fra oppstart til effekt (avgjør hvor langt frem vi må predikere). ~381 liter totalt vannvolum gir betydelig termisk masse.
- [ ] **Temperaturgrenser**: Hvilket område er "farlig"? (typisk 0 til -5 °C med fukt)
- [ ] **Prioritet**: Optimalisere for energibruk eller for 100% sikkerhet mot is?

## E. Funksjonelle ønsker — gjenstår

- [ ] **Varsling**: Ønskes varsling på mobil (SMS/push) ved oppstart, feil, etc.?
- [ ] **Fjernstyring**: Skal systemet kunne styres fra utenfor lokalt nett?
- [ ] **Logging**: Hvor lenge skal historikk lagres?
- [ ] **Integrasjoner**: Ønskes integrasjon med smarthus (Home Assistant, etc.)?

## F. Temperaturfølere — sjekkes fysisk

- [ ] **Type rørfølere**: Ukjent — sjekk merkingen (DS18B20 har 3 ledere, PT1000 har 2-4, NTC har 2)
- [ ] **Tilkobling**: Har de kontakt/plugg, eller er de hardkoblet?

### Slik sjekker du sensortype

1. **DS18B20**: Digital, 3 ledere (rød/svart/gul). Liten metallhylse. Kobles rett på GPIO.
2. **PT1000/PT100**: 2 eller 4 ledere, vanligvis hvit kabel. Trenger ADC (analog-digital-konverter).
3. **NTC**: 2 ledere, ofte svart kabel. Trenger ADC.
4. **Sjekk merking**: Se etter tekst på sensorkroppen eller i dokumentasjon fra installatør.

## Referansedokumentasjon

- [docs/CZ-TAW1-OI-1.pdf](docs/CZ-TAW1-OI-1.pdf) — Panasonic CZ-TAW1 nettverksadapter (ikke kompatibel med G-gen)
- [docs/SM-WHMXC09G3E5_WH-MXC12G6E5.pdf](docs/SM-WHMXC09G3E5_WH-MXC12G6E5.pdf) — Servicemanual for varmepumpen
