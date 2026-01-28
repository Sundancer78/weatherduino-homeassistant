from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import (
    CONF_PATH,
    CONF_SCAN_INTERVAL,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def _normalize_path(raw: str | None) -> str:
    """
    Normalize the JSON path:

    - "" (empty/whitespace) -> "/"  (root; needed for WeatherDisplay)
    - otherwise ensure leading "/"
    """
    if raw is None:
        raw = ""

    path = str(raw).strip()

    if path == "":
        return "/"

    if not path.startswith("/"):
        path = "/" + path

    return path


class WeatherDuinoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            host: str = user_input[CONF_HOST].strip()
            port: int = int(user_input.get(CONF_PORT, DEFAULT_PORT))

            # IMPORTANT:
            # If the user clears the optional field, HA may omit the key entirely.
            # So we default to "" here, not DEFAULT_PATH.
            raw_path = user_input.get(CONF_PATH, "")
            path: str = _normalize_path(raw_path)

            scan_interval: int = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

            await self.async_set_unique_id(f"weatherduino-{host}:{port}{path}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=host,
                data={
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_PATH: path,
                    CONF_SCAN_INTERVAL: scan_interval,
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                # Show default /json, but allow user to clear it (=> "/")
                vol.Optional(CONF_PATH, default=DEFAULT_PATH): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WeatherDuinoOptionsFlow(config_entry)


class WeatherDuinoOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Same trick for options: missing key should be treated as empty => "/"
            raw_path = user_input.get(CONF_PATH, "")
            path: str = _normalize_path(raw_path)

            scan_interval: int = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

            return self.async_create_entry(
                title="",
                data={
                    CONF_PATH: path,
                    CONF_SCAN_INTERVAL: scan_interval,
                },
            )

        current_path = self._config_entry.options.get(
            CONF_PATH, self._config_entry.data.get(CONF_PATH, DEFAULT_PATH)
        )
        current_scan = self._config_entry.options.get(
            CONF_SCAN_INTERVAL, self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        schema = vol.Schema(
            {
                vol.Optional(CONF_PATH, default=current_path): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=current_scan): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
