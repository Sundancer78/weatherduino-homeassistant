# custom_components/weatherduino/coordinator.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PATH, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_PATH, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeatherDuinoConfig:
    host: str
    path: str
    scan_interval: int


class WeatherDuinoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch WeatherDuino JSON from local webserver."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry

        host = entry.data.get(CONF_HOST, "")
        path = entry.data.get(CONF_PATH, DEFAULT_PATH)
        scan = int(entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 30)))

        self.wd_config = WeatherDuinoConfig(host=host, path=path, scan_interval=scan)

        self.base_url = f"http://{self.wd_config.host}"
        self.url = f"{self.base_url}{self.wd_config.path}"

        # Will be updated after first successful fetch
        self.device_id: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self.wd_config.host}",
            update_interval=timedelta(seconds=self.wd_config.scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(self.url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                data: dict[str, Any] = await resp.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error fetching/parsing WeatherDuino JSON from {self.url}: {err}") from err

        # Prefer the device-reported ID for naming
        if isinstance(data.get("ID"), str) and data["ID"].strip():
            self.device_id = data["ID"].strip()
        else:
            self.device_id = self.wd_config.host

        return data
