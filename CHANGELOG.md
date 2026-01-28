# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project follows [Semantic Versioning](https://semver.org/).

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

