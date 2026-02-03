# WeatherDuino (Local JSON) – Home Assistant Integration

A custom Home Assistant integration for **WeatherDuino** receivers/monitors that expose their data via a local HTTP JSON endpoint (default: `/json`).

The integration is configured entirely via **Config Flow (UI)**:  
enter the IP/hostname → sensors are created automatically.

Repository:  
https://github.com/Sundancer78/weatherduino-homeassistant

---

## Supported devices / JSON formats

### WeatherDuino 4Pro (Dual Band RX)
- Default JSON path: `/json` (depending on firmware sometimes `/`)
- Provides the full receiver payload: temperature, humidity, pressure, wind, rain, solar/UV, air quality, extra sensors, soil sensors (depending on setup)

**Important field meanings (4Pro):**
- `TID` = **Device Type / Receiver Type** (e.g. `0xA0` for 4Pro Dual Band RX)
- `ts` = timestamp (receiver local time)
- Most sensor values are scaled by 10 in JSON (→ shown as real values in Home Assistant)

---

### WeatherDuino WeatherDisplay 4Pro
- JSON path is typically the root endpoint: `/`
- Payload example:  
  `{"ID":"WD-WeatherDisplay-4Pro","TID":7,"T":143,"H":775}`
- Mapped sensors:
  - Temperature (`T` / 10)
  - Humidity (`H` / 10)
  - Device Type (`TID`, diagnostic)

---

### WeatherDuino AQM2
- JSON path typically: `/`
- Payload example:
  `{"ID":"AQM2out-pWS_Sun_Dancer","TID":10,"T":-36,"H":510,"PM25":408,"PM100":507,"AVG_M":2,"PM25AQI":630,"PM100AQI":380,"CO2":410}`

**Mapped sensors:**
- Temperature (`T` / 10)
- Humidity (`H` / 10)
- PM2.5 (`PM25` / 10)
- PM10 (`PM100` / 10)
- CO2 (`CO2`, ppm)
- `AVG_M` = **AQ_AVGMODE** (diagnostic)
  - 1 = 1 Hour Average
  - 2 = 3 Hours Average
  - 3 = Nowcast 12H
  - 4 = 24 Hours Average
- PM AQI fields are scaled by 10 (→ shown as real values):
  - `PM25AQI` / 10
  - `PM100AQI` / 10
- Device Type (`TID`, diagnostic)

> Note: The integration shows the values as delivered by the device firmware.  
> AQI standards/modes are handled in firmware.

---

### WeatherDuino AQM3
- JSON path typically: `/`
- Payload example:
  `{"ID":"AQM3in-pWS_Sun_Dancer","TID":11,"ts":1770066996,"T":215,"H":377,"P":9942,"PM25_last":308,"PM100_last":408,"PM25_3H":392,"PM100_3H":498,"CO2":404}`

**Mapped sensors:**
- Temperature (`T` / 10)
- Humidity (`H` / 10)
- Pressure (`P` / 10)
- CO2 (`CO2`, ppm)
- PM series (all / 10):
  - `PM25_last`, `PM100_last`
  - `PM25_1H`, `PM100_1H`
  - `PM25_3H`, `PM100_3H`
  - `PM25_12H`, `PM100_12H`
  - `PM25_24H`, `PM100_24H`
- Timestamp (`ts`, diagnostic)
- Device Type (`TID`, diagnostic)

---

## Features

- Fully local
- Config Flow (UI-based setup)
- Automatic sensor creation (based on detected JSON format)
- Clean naming (stable entity IDs)
- Correct scaling & display precision:
  - Scaled values (e.g. /10): shown with **2 decimals**
  - Integer values (e.g. CO2 ppm, wind direction): shown with **0 decimals**
- Wind, rain, air quality, soil & extra sensors supported (depending on device)

---

## Requirements

- Home Assistant (Core / OS / Supervised)
- WeatherDuino reachable in the local network
- JSON endpoint available (default: `/json`)
- Recorder enabled (recommended for charts)

---

## Installation

### HACS (Custom Repository)

1. HACS → **Integrations**
2. Menu (⋮) → **Custom repositories**
3. Add repository URL  
   `https://github.com/Sundancer78/weatherduino-homeassistant`  
   Category: **Integration**
4. Install
5. Restart Home Assistant
6. Settings → **Devices & Services** → **Add Integration**
7. Search for **WeatherDuino (Local JSON)**

---

## Configuration (UI)

- Host / IP (e.g. `192.168.1.240`)
- Port (default: `80`)
- Path (default: `/json`)  
  - Some devices/firmwares use root `/` (e.g. WeatherDisplay, some AQM builds)
- Scan interval (default: `30s`)

---

## Recommended Lovelace Cards (HACS)

The dashboards below use:

- **Mushroom Cards**
- **ApexCharts Card**
- **Windrose Card**
- **Rain Gauge Card**
- **Layout Card**

Optional:
- **card-mod**

---

## Screenshots

Screenshots are located in the `Screenshots/` folder.

### 1) Overview – Classic Dashboard
![Overview](Screenshots/lovelace-cards.png)

### 2) Status & Quick Values (Mushroom + ApexCharts)
![Status](Screenshots/lovelace-cards1.png)

### 3) Rain Monitoring (Rain Gauge + ApexCharts)
![Rain](Screenshots/lovelace-cards2.png)

### 4) Wind Analysis (Windrose)
![Windrose](Screenshots/windrose.png)

### 5) All Sensors (Entities)
![Sensors](Screenshots/Sensor.png)

---

## Disclaimer

This is an **unofficial Home Assistant integration** developed by the community.  
It has **no relation to the official WeatherDuino manufacturer** and is **not supported or endorsed by them**.

The integration communicates exclusively with the device’s local JSON interface.
