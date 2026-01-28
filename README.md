# weatherduino-homeassistant
weatherduino-homeassistant-integration

# WeatherDuino (Local JSON) – Home Assistant Integration

A custom Home Assistant integration for **WeatherDuino** receivers that expose their data via a local HTTP JSON endpoint (default: `/json`).

The integration is set up entirely via **Config Flow (UI)**:  
enter the IP/hostname → sensors are created automatically.

Repository:  
https://github.com/Sundancer78/weatherduino-homeassistant

---

## Features

- ✅ Fully local (no cloud dependency)
- ✅ Config Flow (UI-based setup)
- ✅ Automatic sensor creation
- ✅ Clean naming:
  - Device name from JSON field `ID` (fallback: host)
  - Sensor names without `WeatherDuino <IP>` prefixes
- ✅ Ready-to-use Lovelace dashboard examples
- ✅ Wind, rain, air quality, soil & extra sensors supported

---

## Requirements

- Home Assistant (Core / OS / Supervised)
- WeatherDuino reachable in your local network
- JSON endpoint available (default: `/json`)
- Recorder enabled (recommended for charts/history)

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

### Manual Installation

1. Copy  
   `custom_components/weatherduino/`  
   into  
   `config/custom_components/weatherduino/`
2. Restart Home Assistant
3. Add the integration via UI

---

## Configuration (UI)

During setup you can configure:

- **Host/IP** (e.g. `192.168.1.240`)
- **Port** (default: `80`)
- **Path** (default: `/json`)
- **Scan interval** (default: `30s`)

---

## Recommended Lovelace Cards (HACS)

The dashboards shown below use the following cards:

- **Mushroom Cards** – clean tiles & chips
- **ApexCharts Card** – advanced charts, thin lines, grouping
- **Windrose Card** – wind direction distribution with speed bins
- **Rain Gauge Card** – rain “today” visualization
- **Layout Card** – stable, responsive multi-column layouts

Optional:
- **card-mod** – colored warning chips (rain, CO₂, etc.)

---

## Screenshots

> Screenshots are located in the `Screenshots/` folder.

### 1) Overview – Classic Cards
![WeatherDuino Dashboard Overview](Screenshots/lovelace-cards.png)

### 2) Status & Quick Values (Mushroom + ApexCharts)
![WeatherDuino Status Cards](Screenshots/lovelace-cards1.png)

### 3) Rain Monitoring (Rain Gauge + ApexCharts)
![WeatherDuino Rain Monitoring](Screenshots/lovelace-cards2.png)

### 4) Wind Analysis (Windrose 24h / 4h)
![WeatherDuino Windrose](Screenshots/windrose.png)

### 5) Sensors (Entities List)
![WeatherDuino Sensors](Screenshots/Sensor.png)

---

# Lovelace YAML – Code per Screenshot

> **Entity IDs used in the examples**  
> (adjust if your IDs differ):
>
> - `sensor.rx_weatherduino_4pro_outside_temperature`
> - `sensor.rx_weatherduino_4pro_outside_humidity`
> - `sensor.rx_weatherduino_4pro_pressure`
> - `sensor.rx_weatherduino_4pro_wind_speed`
> - `sensor.rx_weatherduino_4pro_wind_gust`
> - `sensor.rx_weatherduino_4pro_wind_direction`
> - `sensor.rx_weatherduino_4pro_rain_today`
> - `sensor.rx_weatherduino_4pro_rain_rate`
> - `sensor.rx_weatherduino_4pro_solar_radiation`
> - `sensor.rx_weatherduino_4pro_co2`
> - `sensor.rx_weatherduino_4pro_pm2_5`
> - `sensor.rx_weatherduino_4pro_pm10`
> - `sensor.rx_weatherduino_4pro_air_quality_index`

---

## Screenshot 1 – Classic Overview  
`Screenshots/lovelace-cards.png`

**Layout:**  
Left = quick values,  
Center = history graphs,  
Right = air quality entities.

```yaml
type: custom:layout-card
layout_type: grid
layout:
  grid-template-columns: 1fr 1fr 1fr
  grid-gap: 16px
cards:
  - type: vertical-stack
    cards:
      - type: grid
        columns: 3
        square: false
        cards:
          - type: sensor
            entity: sensor.rx_weatherduino_4pro_outside_temperature
            name: Outside Temperature
          - type: sensor
            entity: sensor.rx_weatherduino_4pro_outside_humidity
            name: Outside Humidity
          - type: sensor
            entity: sensor.rx_weatherduino_4pro_pressure
            name: Pressure

      - type: grid
        columns: 3
        square: false
        cards:
          - type: gauge
            entity: sensor.rx_weatherduino_4pro_wind_speed
            name: Wind
            min: 0
            max: 25
          - type: gauge
            entity: sensor.rx_weatherduino_4pro_wind_gust
            name: Gust
            min: 0
            max: 35
          - type: sensor
            entity: sensor.rx_weatherduino_4pro_wind_direction
            name: Wind Direction

      - type: grid
        columns: 3
        square: false
        cards:
          - type: sensor
            entity: sensor.rx_weatherduino_4pro_rain_today
            name: Rain Today
          - type: gauge
            entity: sensor.rx_weatherduino_4pro_rain_rate
            name: Rain Rate
            min: 0
            max: 50
          - type: sensor
            entity: sensor.rx_weatherduino_4pro_solar_radiation
            name: Solar Radiation

  - type: vertical-stack
    cards:
      - type: history-graph
        title: History (12h)
        hours_to_show: 12
        entities:
          - entity: sensor.rx_weatherduino_4pro_outside_temperature
            name: Outside °C
      - type: history-graph
        title: Pressure (12h)
        hours_to_show: 12
        entities:
          - entity: sensor.rx_weatherduino_4pro_pressure
            name: hPa

  - type: entities
    title: Air Quality
    show_header_toggle: false
    entities:
      - sensor.rx_weatherduino_4pro_co2
      - sensor.rx_weatherduino_4pro_pm2_5
      - sensor.rx_weatherduino_4pro_pm10
      - sensor.rx_weatherduino_4pro_air_quality_index
