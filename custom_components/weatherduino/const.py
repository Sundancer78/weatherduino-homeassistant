DOMAIN = "weatherduino"

PLATFORMS: list[str] = ["sensor"]

CONF_PATH = "path"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_DEVICE_TYPE = "device_type"

DEFAULT_PORT = 80
DEFAULT_PATH = "/json"
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_DEVICE_TYPE = "auto"

ATTRIBUTION = "Data provided by WeatherDuino Local JSON"

# Device type selector values
DEVICE_TYPE_AUTO = "auto"
DEVICE_TYPE_4PRO = "4pro"
DEVICE_TYPE_WEATHERDISPLAY = "weatherdisplay"
DEVICE_TYPE_AQM2 = "aqm2"
DEVICE_TYPE_AQM3 = "aqm3"

DEVICE_TYPES = [
    DEVICE_TYPE_AUTO,
    DEVICE_TYPE_4PRO,
    DEVICE_TYPE_WEATHERDISPLAY,
    DEVICE_TYPE_AQM2,
    DEVICE_TYPE_AQM3,
]