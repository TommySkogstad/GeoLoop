# GeoLoop — Oppsettguide

Steg-for-steg-guide for å sette opp Raspberry Pi 3B+ med temperatursensorer, RPi Relay Board og GeoLoop-programvaren.

---

## Maskinvareoversikt

| # | Komponent | Modell | Merknad |
|---|-----------|--------|---------|
| 1 | Raspberry Pi 3B+ | BCM2837B0, 1 GB RAM | Styringsenhet |
| 2 | RPi Relay Board | 3 kanaler (HAT-format) | Sitter direkte på GPIO-header |
| 3 | Open-Smart GPIO Expansion Board | | Ekstra GPIO-pinner til sensorer |
| 4 | Micro-SD-kort (32 GB+) | SanDisk Extreme anbefalt | OS og programvare |
| 5 | USB Micro-B strømforsyning (5V/2.5A) | Offisiell RPi 3B+ PSU | Strøm til RPi |
| 6 | DS18B20 temperatursensorer (vanntett) | Rørfølere, 5 stk | Tur/retur + tank |
| 7 | 4,7 kΩ motstand | For 1-Wire pull-up | 1 stk |
| 8 | Ethernet-kabel eller WiFi-tilgang | Cat5e/Cat6 | Nettverk |

---

## Del 1: Raspberry Pi grunnoppsett

### 1.1 Installer operativsystem

1. Last ned [Raspberry Pi Imager](https://www.raspberrypi.com/software/) på din PC/Mac
2. Sett inn micro-SD-kortet i PC-en
3. I Imager:
   - Velg **Raspberry Pi OS Lite (64-bit)** (vi trenger ikke desktop)
   - Klikk tannhjulet og konfigurer:
     - Brukernavn og passord
     - WiFi (SSID + passord) hvis du ikke bruker Ethernet
     - Aktiver SSH
     - Sett riktig tidssone (`Europe/Oslo`)
4. Skriv til SD-kortet

### 1.2 Første oppstart

1. Sett SD-kortet i RPi
2. Koble til Ethernet (eller bruk WiFi fra steg 1.1)
3. Koble til strøm
4. Finn RPi-ens IP-adresse (sjekk ruteren, eller bruk `ping raspberrypi.local`)
5. SSH inn:
   ```bash
   ssh brukernavn@raspberrypi.local
   ```

### 1.3 Oppdater systemet

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv git
```

---

## Del 2: Temperatursensorer

5 temperatursensorer plasseres i systemet. Hvis sensorene er DS18B20 (1-Wire), kobles alle parallelt på samme datapinne.

### 2.1 Sensorplassering

| # | Plassering | Formål |
|---|------------|--------|
| T1 | Inn til varmesløyfe (bakke) | Turtemperatur til bakken |
| T2 | Ut av varmesløyfe (bakke) | Returtemperatur fra bakken |
| T3 | Inn til varmepumpe | Returvann til VP |
| T4 | Ut av varmepumpe | Turvann fra VP |
| T5 | Vanntank | Buffertemperatur |

### 2.2 Koblingsskjema (DS18B20)

```
DS18B20 (x5)         Raspberry Pi 3B+
─────────────        ──────────────────
VDD (rød)    ───────  3.3V (pin 1)
GND (svart)  ───────  GND  (pin 6)
DATA (gul)   ───┬───  GPIO4 (pin 7)
                │
                ├── 4,7 kΩ motstand ── 3.3V (pin 1)
                │
           (pull-up, 1 stk for alle sensorer)
```

> **Tips:** Alle 5 DS18B20-sensorer kobles parallelt på samme datapinne (GPIO4). Hver sensor har en unik ID som brukes til å identifisere dem.

### 2.3 Aktiver 1-Wire

1. Rediger boot-konfig:
   ```bash
   sudo nano /boot/firmware/config.txt
   ```
2. Legg til nederst:
   ```
   dtoverlay=w1-gpio,gpiopin=4
   ```
3. Start på nytt:
   ```bash
   sudo reboot
   ```

### 2.4 Verifiser sensorene

```bash
# Last 1-Wire-moduler
sudo modprobe w1-gpio
sudo modprobe w1-therm

# List sensorer (skal vise en mappe per sensor, f.eks. 28-xxxxxxxxxxxx)
ls /sys/bus/w1/devices/

# Les temperatur fra alle sensorer
cat /sys/bus/w1/devices/28-*/w1_slave
```

Forventet output (siste linje per sensor):
```
t=21375
```
Det betyr 21,375 °C.

> **Merk:** Hvis rørfølerne er PT1000 eller NTC (ikke DS18B20), trengs en ADC-konverter (analog-digital). Se seksjon F i [TODO-avklaringer.md](../TODO-avklaringer.md) for hvordan du identifiserer sensortypen.

---

## Del 3: RPi Relay Board

RPi Relay Board er et HAT-format kort som sitter direkte på GPIO-headeren til RPi 3B+. Det har 3 uavhengige relékanaler.

### 3.1 Montering

1. Slå av RPi
2. Sett RPi Relay Board forsiktig ned på GPIO-headeren
3. Sjekk at alle pinner sitter riktig

> **NB:** GPIO-pinnene som relay board-et bruker varierer mellom produsenter. Sjekk databladet for ditt spesifikke kort og noter hvilke GPIO-pinner som styrer kanal 1, 2 og 3.

### 3.2 Relékanaler

| Kanal | Funksjon | Tilkobling |
|-------|----------|------------|
| 1 | Varmepumpe ON/OFF | VP klemme 17/18 (ekstern kontrollkabel) |
| 2 | Ekstern sirkulasjonspumpe | Separat styring |
| 3 | Ledig | Reservert for fremtidig bruk (kolber) |

### 3.3 Koble relé til varmepumpe

VP-ens ekstern kontrollkabel (2 ledere fra klemme 17/18) kobles til relé kanal 1:

```
Panasonic WH-MXC12G6E5          RPi Relay Board
Klemmerekke                      Kanal 1
┌──────────────────┐             ┌─────────────────┐
│  Klemme 17 ──────┼─── leder ──┤ NO              │
│  Klemme 18 ──────┼─── leder ──┤ COM             │◄── GPIO fra RPi
└──────────────────┘             └─────────────────┘

Relé lukket (17↔18 kortsluttet) → VP er PÅ
Relé åpent  (17↔18 brutt)       → VP er AV
```

> **Viktig:** Fjern fabrikkjumperen mellom klemme 17 og 18 på VP-en før du kobler til reléet. Klemme 17/18 er lavspenning potensialfri kontakt — ingen 230V involvert, trygt å koble selv.

### 3.4 Test reléet

```bash
# Erstatt GPIO_PIN med faktisk pinne for kanal 1 på ditt relay board
GPIO_PIN=17

echo $GPIO_PIN | sudo tee /sys/class/gpio/export
echo out | sudo tee /sys/class/gpio/gpio${GPIO_PIN}/direction

# Slå på (du skal høre et klikk fra reléet)
echo 1 | sudo tee /sys/class/gpio/gpio${GPIO_PIN}/value

# Slå av
echo 0 | sudo tee /sys/class/gpio/gpio${GPIO_PIN}/value

# Rydd opp
echo $GPIO_PIN | sudo tee /sys/class/gpio/unexport
```

---

## Del 4: Installer GeoLoop

### 4.1 Klon prosjektet

```bash
cd ~
git clone <repo-url> GeoLoop
cd GeoLoop
```

### 4.2 Kjør installasjonscriptet

```bash
sudo bash scripts/install.sh
```

Dette gjør:
- Oppretter Python virtualenv
- Installerer alle avhengigheter
- Kopierer `config.example.yaml` til `config.yaml`
- Registrerer `geoloop` som systemd-tjeneste

### 4.3 Konfigurer

Rediger `config.yaml` med dine verdier:

```bash
nano ~/GeoLoop/config.yaml
```

Se [config.example.yaml](../config.example.yaml) for alle tilgjengelige innstillinger.

> **Finn koordinater:** Gå til [norgeskart.no](https://norgeskart.no), høyreklikk på din lokasjon, og kopier koordinatene.

### 4.4 Start tjenesten

```bash
sudo systemctl start geoloop
```

### 4.5 Verifiser at alt kjører

```bash
# Sjekk tjenestestatus
sudo systemctl status geoloop

# Sjekk logg
journalctl -u geoloop -f

# Test API-et (fra RPi eller annen maskin på nettverket)
curl http://raspberrypi.local:8000/api/status
```

---

## Del 5: Nettverkstilgang

For å nå dashboardet fra andre enheter på nettverket:

1. Finn RPi-ens IP: `hostname -I`
2. Åpne nettleser på PC/mobil: `http://<ip-adresse>:8000/api/status`

---

## Systemdiagram

Buffertanken (200 L, udelt) er sentral node. To separate kretser møtes i tanken.

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

Relé K1 ──── VP klemme 17/18 (ON/OFF)
Relé K2 ──── Ekstern sirkulasjonspumpe
Relé K3 ──── Ledig (kolber i fremtiden)
```

**Vannvolum totalt: ~421 liter** (181 L sløyfe + 200 L buffer + 10 L kolbetank + ~30 L internrør)

---

## Feilsøking

| Problem | Løsning |
|---------|---------|
| Sensor vises ikke i `/sys/bus/w1/devices/` | Sjekk kabling og at `dtoverlay=w1-gpio` er i config.txt. Reboot. |
| Relé klikker ikke | Sjekk GPIO-pinne mot databladet for ditt relay board. |
| VP starter ikke når relé lukker | Sjekk at fabrikkjumper mellom klemme 17/18 er fjernet. |
| `geoloop`-tjenesten starter ikke | Kjør `journalctl -u geoloop -e` for feilmelding. Sjekk at config.yaml er gyldig. |
| Kan ikke nå web-API fra annen maskin | Sjekk at `host: "0.0.0.0"` i config. Sjekk brannmur: `sudo ufw status`. |
| Værdata returnerer feil | Sjekk at `user_agent` er satt (api.met.no krever dette). |

## Referansedokumentasjon

- [docs/CZ-TAW1-OI-1.pdf](CZ-TAW1-OI-1.pdf) — Panasonic CZ-TAW1 nettverksadapter (ikke kompatibel med G-gen)
- [docs/SM-WHMXC09G3E5_WH-MXC12G6E5.pdf](SM-WHMXC09G3E5_WH-MXC12G6E5.pdf) — Servicemanual for Panasonic WH-MXC12G6E5
