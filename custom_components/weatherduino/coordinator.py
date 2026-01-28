from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_PATH, CONF_SCAN_INTERVAL, DEFAULT_PATH, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeatherDuinoConfig:
    host: str
    port: int
    path: str
    scan_interval: int


def _normalize_path(raw: str | None) -> str:
    if raw is None:
        return DEFAULT_PATH
    path = str(raw).strip()
    if path == "":
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path


def _has_any(data: dict[str, Any], keys: list[str]) -> bool:
    return any(k in data for k in keys)


def _looks_like_4pro_receiver(data: dict[str, Any]) -> bool:
    # Typical 4Pro receiver keys
    return _has_any(data, ["Tout", "Hout", "Wsp", "Wdir", "Rtd", "Rfr", "Tin", "Hin"])


def _looks_like_weatherdisplay(data: dict[str, Any]) -> bool:
    # WeatherDisplay example: {"ID":"...","TID":7,"T":143,"H":775}
    return ("T" in data and "H" in data) and not _looks_like_4pro_receiver(data)


class WeatherDuinoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch WeatherDuino JSON from local webserver."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        host = entry.data.get(CONF_HOST, "")
        port = int(entry.data.get(CONF_PORT, DEFAULT_PORT))

        path = entry.options.get(CONF_PATH, entry.data.get(CONF_PATH, DEFAULT_PATH))
        path = _normalize_path(path)

        scan = int(entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 30)))

        self.wd_config = WeatherDuinoConfig(host=host, port=port, path=path, scan_interval=scan)

        if self.wd_config.port and self.wd_config.port != 80:
            self.base_url = f"http://{self.wd_config.host}:{self.wd_config.port}"
        else:
            self.base_url = f"http://{self.wd_config.host}"

        self.url = f"{self.base_url}{self.wd_config.path}"

        # Will be updated after first successful fetch
        self.device_id: str | None = None

        # Used for device_info configuration_url handling
        self.is_weatherdisplay: bool = False

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self.wd_config.host}",
            update_interval=timedelta(seconds=self.wd_config.scan_interval),
        )

    @property
    def configuration_url(self) -> str | None:
        """
        Return a clickable configuration URL for the HA device page.

        - 4Pro receiver: has a web UI under /weather
        - WeatherDisplay: no web UI -> return None (no link in HA)
        """
        if self.is_weatherdisplay:
            return None
        return f"{self.base_url}/weather"

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(self.url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                data: dict[str, Any] = await resp.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error fetching/parsing WeatherDuino JSON from {self.url}: {err}") from err

        # Detect device type for config URL behavior
        self.is_weatherdisplay = _looks_like_weatherdisplay(data)

        # Prefer device-reported ID for naming
        if isinstance(data.get("ID"), str) and data["ID"].strip():
            self.device_id = data["ID"].strip()
        else:
            self.device_id = self.wd_config.host

        return data
