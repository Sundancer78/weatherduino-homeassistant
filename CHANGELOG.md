# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project follows [Semantic Versioning](https://semver.org/).

---

## [0.5.7] – 2026-02-03

### Added
- Added appropriate Material Design Icons to all WeatherDuino sensor entities
- Icons are now defined directly in `SensorEntityDescription` and bound to the correct entity keys and unique IDs

### Changed
- Improved overall UI clarity and readability in Home Assistant dashboards

### Notes
- No functional changes to sensor logic or data processing
- Existing entities keep their IDs; no migration required

---

## [0.5.6] – 2026-02-03

### Added
- Full multi-device support for WeatherDuino **4Pro**, **WeatherDisplay**, **AQM2** and **AQM3**
- Human-readable interpretation of `AVG_M` as **AQ_AVGMODE** for AQM2 devices
- Complete device documentation added to the README

### Fixed
- Restored and unified sensor support across all supported device types
- Fixed all scaling rules according to firmware specifications (×10 → ÷10)
- Corrected CO₂ display to integer **ppm** values (no decimals)
- Applied consistent display precision:
  - 2 decimals for scaled sensor values
  - 0 decimals for integer values (e.g. CO₂, wind direction)
- Corrected `TID` meaning to represent the **device / receiver type**
- Ensured AQI values are shown raw as provided by the device firmware

---

## [0.3.3] – 2026-01-28

### Added
- Device-specific configuration URLs in the Home Assistant device page
  - WeatherDuino 4Pro opens the built-in web interface at `/weather`
  - WeatherDisplay devices no longer show a non-functional web link

### Changed
- Improved device type detection based on the reported JSON payload
- Refined device information displayed in Home Assistant
- Internal cleanup and refinements for HACS submission

---

## [0.3.2] – 2026-01-28

### Added
- Support for **WeatherDuino WeatherDisplay** JSON format
  - Temperature (`T`)
  - Humidity (`H`)
  - Transmitter ID (`TID`, diagnostic)
- Allow empty JSON path in the config flow to use the root endpoint (`/`)
  - Required for WeatherDisplay devices

### Fixed
- Restored full WeatherDuino **4Pro sensor set** after refactoring
- Improved config flow compatibility with newer Home Assistant versions
- Prevented invalid defaulting to `/json` when path field is cleared

### Changed
- Cleaned up sensor naming
  - Transmitter ID is no longer shown in the visible sensor name
  - Unique IDs still include TID to support multiple transmitters
- Improved UI descriptions and translations (EN / DE)
- Updated documentation to clearly describe supported devices and endpoints

---

## [0.3.1] – 2026-01-27

### Fixed
- Sensor naming no longer includes IP address
- Improved device naming using the ID reported by the WeatherDuino device
- Minor internal cleanup and documentation updates

---

## [0.3.0] – 2026-01-26

### Added
- Initial public release
- Home Assistant Config Flow (UI-based setup)
- Automatic sensor creation for WeatherDuino 4Pro
- Lovelace dashboard examples (Windrose, ApexCharts, Rain Gauge, Mushroom Cards)

---
