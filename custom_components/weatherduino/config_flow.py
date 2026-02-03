from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_PATH,
    CONF_SCAN_INTERVAL,
    CONF_DEVICE_TYPE,
    DEFAULT_PORT,
    DEFAULT_PATH,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_DEVICE_TYPE,
    DEVICE_TYPES,
)


def _normalize_path(raw: str | None) -> str:
    """Normalize path input:
    - empty => "/"
    - ensure leading "/"
    """
    if raw is None:
        return DEFAULT_PATH
    path = str(raw).strip()
    if path == "":
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path


class WeatherDuinoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = str(user_input.get(CONF_HOST, "")).strip()
            if not host:
                errors["base"] = "invalid_input"
            else:
                port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
                path = _normalize_path(user_input.get(CONF_PATH, DEFAULT_PATH))
                device_type = user_input.get(CONF_DEVICE_TYPE, DEFAULT_DEVICE_TYPE)
                scan_interval = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=host,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_PATH: path,
                        CONF_DEVICE_TYPE: device_type,
                        CONF_SCAN_INTERVAL: scan_interval,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_PATH, default=DEFAULT_PATH): str,
                vol.Optional(CONF_DEVICE_TYPE, default=DEFAULT_DEVICE_TYPE): vol.In(DEVICE_TYPES),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return WeatherDuinoOptionsFlowHandler(config_entry)


class WeatherDuinoOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            path = _normalize_path(user_input.get(CONF_PATH))
            device_type = user_input.get(CONF_DEVICE_TYPE, DEFAULT_DEVICE_TYPE)
            scan_interval = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

            return self.async_create_entry(
                title="",
                data={
                    CONF_PATH: path,
                    CONF_DEVICE_TYPE: device_type,
                    CONF_SCAN_INTERVAL: scan_interval,
                },
            )

        current_path = self._entry.options.get(CONF_PATH, self._entry.data.get(CONF_PATH, DEFAULT_PATH))
        current_device_type = self._entry.options.get(CONF_DEVICE_TYPE, self._entry.data.get(CONF_DEVICE_TYPE, DEFAULT_DEVICE_TYPE))
        current_scan = self._entry.options.get(CONF_SCAN_INTERVAL, self._entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

        schema = vol.Schema(
            {
                vol.Optional(CONF_PATH, default=current_path): str,
                vol.Optional(CONF_DEVICE_TYPE, default=current_device_type): vol.In(DEVICE_TYPES),
                vol.Optional(CONF_SCAN_INTERVAL, default=current_scan): int,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)