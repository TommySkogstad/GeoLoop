# GeoLoop — Oppsettguide

Steg-for-steg-guide for å sette opp Raspberry Pi med temperatursensorer, relé og GeoLoop-programvaren.

---

## Handleliste

| # | Komponent | Eksempel | Ca. pris |
|---|-----------|----------|----------|
| 1 | Raspberry Pi 4 eller 5 (2 GB+ RAM) | RPi 4 Model B | 500–800 kr |
| 2 | Micro-SD-kort (32 GB+) | SanDisk Extreme | 100 kr |
| 3 | USB-C strømforsyning (5V/3A) | Offisiell RPi PSU | 100 kr |
| 4 | DS18B20 temperatursensor (vanntett) | Med 1 m kabel | 50–80 kr/stk |
| 5 | 4,7 kΩ motstand | For 1-Wire pull-up | 5 kr |
| 6 | Relékort (1-kanals, 3.3V-kompatibelt) | SRD-05VDC | 50 kr |
| 7 | Breadboard + jumper-kabler | Standard sett | 80 kr |
| 8 | Ethernet-kabel eller WiFi-tilgang | Cat5e/Cat6 | — |
| 9 | (Valgfritt) Kapsling for RPi | Aluminium/plast | 100 kr |

> **Merk:** For styring av 230V kontaktor trenger du et relé dimensjonert for nettstrøm, og arbeidet bør utføres av autorisert elektriker.

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

## Del 2: Koble til DS18B20 temperatursensor

DS18B20 bruker 1-Wire-protokollen og trenger kun én datapinne.

### 2.1 Koblingsskjema

```
DS18B20              Raspberry Pi
─────────            ─────────────
VDD (rød)    ───────  3.3V (pin 1)
GND (svart)  ───────  GND  (pin 6)
DATA (gul)   ───────  GPIO4 (pin 7)
                 │
                 ├── 4,7 kΩ motstand ── 3.3V (pin 1)
                 │
            (pull-up)
```

**Pinneoversikt (fysiske pinner):**

```
         3.3V [1]  [2] 5V
   GPIO2/SDA [3]  [4] 5V
   GPIO3/SCL [5]  [6] GND    ← GND her
  GPIO4/1-Wire[7] [8] GPIO14
              ...
```

> **Tips:** Du kan koble flere DS18B20-sensorer parallelt på samme datapinne. Hver sensor har en unik ID.

### 2.2 Aktiver 1-Wire

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

### 2.3 Verifiser sensoren

```bash
# Last 1-Wire-moduler
sudo modprobe w1-gpio
sudo modprobe w1-therm

# List sensorer (skal vise en mappe per sensor, f.eks. 28-xxxxxxxxxxxx)
ls /sys/bus/w1/devices/

# Les temperatur (i milligrader Celsius)
cat /sys/bus/w1/devices/28-*/w1_slave
```

Forventet output (siste linje):
```
t=21375
```
Det betyr 21,375 °C.

---

## Del 3: Koble til relé

Reléet styrer en kontaktor som slår varmepumpen av/på.

### 3.1 Koblingsskjema

```
Relékort             Raspberry Pi
─────────            ─────────────
VCC          ───────  3.3V (pin 17)
GND          ───────  GND  (pin 20)
IN           ───────  GPIO17 (pin 11)
```

> **Viktig:** Noen relékort krever 5V VCC men har 3.3V-kompatibel signalinngang. Sjekk databladet for ditt kort. Bruk 5V (pin 2 eller 4) for VCC hvis nødvendig.

### 3.2 Test reléet

```bash
# Eksporter GPIO17
echo 17 | sudo tee /sys/class/gpio/export
echo out | sudo tee /sys/class/gpio/gpio17/direction

# Slå på (du skal høre et klikk fra reléet)
echo 1 | sudo tee /sys/class/gpio/gpio17/value

# Slå av
echo 0 | sudo tee /sys/class/gpio/gpio17/value

# Rydd opp
echo 17 | sudo tee /sys/class/gpio/unexport
```

### 3.3 Koble relé til kontaktor

```
                    ┌──────────────┐
RPi GPIO17 ──────── │  Relékort    │
                    │              │
                    │  NO ─────────┼──── Kontaktor spole (L)
                    │  COM ────────┼──── Fase (L) fra sikringsskap
                    └──────────────┘

Kontaktor styrer varmepumpe av/på.
```

> **ADVARSEL:** Tilkobling til 230V **skal utføres av autorisert elektriker**. Feilkobling kan forårsake brann eller elektrisk støt.

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

```yaml
location:
  lat: 59.91      # Din breddegrad
  lon: 10.75      # Din lengdegrad

weather:
  user_agent: "GeoLoop/0.1 kontakt@example.com"  # Påkrevd av api.met.no
  poll_interval_minutes: 30

database:
  path: "/home/pi/GeoLoop/geoloop.db"

web:
  host: "0.0.0.0"
  port: 8000
```

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
curl http://raspberrypi.local:8000/api/weather
```

---

## Del 5: Nettverkstilgang

For å nå dashboardet fra andre enheter på nettverket:

1. Finn RPi-ens IP: `hostname -I`
2. Åpne nettleser på PC/mobil: `http://<ip-adresse>:8000/api/status`

---

## Feilsøking

| Problem | Løsning |
|---------|---------|
| Sensor vises ikke i `/sys/bus/w1/devices/` | Sjekk kabling og at `dtoverlay=w1-gpio` er i config.txt. Reboot. |
| Relé klikker ikke | Sjekk at VCC er riktig spenning (3.3V vs 5V). Test med multimeter. |
| `geoloop`-tjenesten starter ikke | Kjør `journalctl -u geoloop -e` for feilmelding. Sjekk at config.yaml er gyldig. |
| Kan ikke nå web-API fra annen maskin | Sjekk at `host: "0.0.0.0"` i config. Sjekk brannmur: `sudo ufw status`. |
| Værdata returnerer feil | Sjekk at `user_agent` er satt (api.met.no krever dette). |
