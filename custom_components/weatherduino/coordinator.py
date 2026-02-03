from __future__ import annotations

from datetime import timedelta
from typing import Any, Literal
import logging

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE_TYPE,
    CONF_PATH,
    CONF_SCAN_INTERVAL,
    DEFAULT_DEVICE_TYPE,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DeviceType = Literal["auto", "4pro", "weatherdisplay", "aqm2", "aqm3", "unknown"]


def _normalize_path(raw: str | None) -> str:
    # IMPORTANT: empty => "/"
    if raw is None:
        return "/"
    raw = str(raw).strip()
    if raw == "":
        return "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    return raw


def _has_any(data: dict[str, Any], keys: list[str]) -> bool:
    return any(k in data for k in keys)


def _detect_device_type(data: dict[str, Any]) -> DeviceType:
    if _has_any(data, ["Wsp", "Wgs", "Wdir", "Rtd", "Rfr"]):
        return "4pro"
    if _has_any(data, ["PM25_last", "PM25_24H", "ts"]):
        return "aqm3"
    if _has_any(data, ["PM25AQI", "PM100AQI", "AVG_M"]):
        return "aqm2"
    if "T" in data and "H" in data:
        return "weatherdisplay"
    return "unknown"


class WeatherDuinoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        self.host: str = entry.data.get(CONF_HOST)
        self.port: int = entry.data.get(CONF_PORT, DEFAULT_PORT)

        # FIX: options should override data, but if options are missing,
        #      fall back to what was entered during setup (entry.data).
        path_from_options = entry.options.get(CONF_PATH)
        path_from_data = entry.data.get(CONF_PATH, DEFAULT_PATH)
        self.path: str = _normalize_path(path_from_options if path_from_options is not None else path_from_data)

        self.scan_interval: int = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, 30),
        )

        self.forced_device_type: DeviceType = entry.options.get(
            CONF_DEVICE_TYPE,
            entry.data.get(CONF_DEVICE_TYPE, DEFAULT_DEVICE_TYPE),
        )

        base = f"http://{self.host}"
        if self.port and self.port != 80:
            base = f"{base}:{self.port}"
        self.url = f"{base}{self.path}"

        self.device_type: DeviceType = "unknown"
        self.device_id: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self.host}",
            update_interval=timedelta(seconds=self.scan_interval),
        )

    @property
    def device_model(self) -> str:
        return {
            "4pro": "WeatherDuino 4Pro",
            "weatherdisplay": "WeatherDuino WeatherDisplay",
            "aqm2": "WeatherDuino 2Pro Air Quality",
            "aqm3": "WeatherDuino Air Quality Monitor 3",
        }.get(self.device_type, "WeatherDuino")

    @property
    def configuration_url(self) -> str | None:
        if self.device_type == "4pro":
            base = f"http://{self.host}"
            if self.port and self.port != 80:
                base = f"{base}:{self.port}"
            return f"{base}/weather"
        return None

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(self.url, timeout=10) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error fetching WeatherDuino JSON: {err}") from err

        detected = _detect_device_type(data)
        self.device_type = (
            detected if self.forced_device_type == "auto" else self.forced_device_type
        )

        self.device_id = data.get("ID", self.host)
        return data
