from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WeatherDuinoCoordinator


# ---------------------------
# Helper structures
# ---------------------------

@dataclass(frozen=True)
class WDValue:
    key: str
    value_fn: Callable[[dict[str, Any]], Any]


def _raw(key: str) -> WDValue:
    return WDValue(key=key, value_fn=lambda data: data.get(key))


def _div10(key: str) -> WDValue:
    return WDValue(
        key=key,
        value_fn=lambda d: (d.get(key) / 10.0) if d.get(key) is not None else None,
    )


def _has_any(data: dict[str, Any], keys: list[str]) -> bool:
    return any(k in data for k in keys)


def _looks_like_4pro_receiver(data: dict[str, Any]) -> bool:
    # Typical 4Pro receiver keys
    return _has_any(data, ["Tout", "Hout", "Wsp", "Wdir", "Rtd", "Rfr", "Tin", "Hin"])


def _looks_like_weatherdisplay(data: dict[str, Any]) -> bool:
    # WeatherDisplay example: {"ID":"...","TID":7,"T":143,"H":775}
    return ("T" in data and "H" in data) and not _looks_like_4pro_receiver(data)


def _get_tid(data: dict[str, Any]) -> int | None:
    tid = data.get("TID")
    if isinstance(tid, (int, float)):
        return int(tid)
    return None


# ---------------------------
# 4Pro Receiver sensors (FULL)
# ---------------------------

SENSORS_4PRO: tuple[tuple[SensorEntityDescription, WDValue], ...] = (
    (
        SensorEntityDescription(
            key="Tin",
            name="Inside Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("Tin"),
    ),
    (
        SensorEntityDescription(
            key="Hin",
            name="Inside Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("Hin"),
    ),
    (
        SensorEntityDescription(
            key="Tout",
            name="Outside Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("Tout"),
    ),
    (
        SensorEntityDescription(
            key="Hout",
            name="Outside Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("Hout"),
    ),
    (
        SensorEntityDescription(
            key="P",
            name="Pressure",
            device_class=SensorDeviceClass.PRESSURE,
            native_unit_of_measurement=UnitOfPressure.HPA,
        ),
        _div10("P"),
    ),
    (
        SensorEntityDescription(
            key="Wsp",
            name="Wind Speed",
            device_class=SensorDeviceClass.WIND_SPEED,
            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        ),
        _div10("Wsp"),
    ),
    (
        SensorEntityDescription(
            key="Wgs",
            name="Wind Gust",
            device_class=SensorDeviceClass.WIND_SPEED,
            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        ),
        _div10("Wgs"),
    ),
    (
        SensorEntityDescription(
            key="Wdir",
            name="Wind Direction",
            native_unit_of_measurement="°",
        ),
        _raw("Wdir"),
    ),
    (
        SensorEntityDescription(
            key="Rtd",
            name="Rain Today",
            native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        ),
        _div10("Rtd"),
    ),
    (
        SensorEntityDescription(
            key="Rfr",
            name="Rain Rate",
            native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        ),
        _div10("Rfr"),
    ),
    (
        SensorEntityDescription(
            key="SR",
            name="Solar Radiation",
            device_class=SensorDeviceClass.IRRADIANCE,
            native_unit_of_measurement="W/m²",
        ),
        _raw("SR"),
    ),
    (
        SensorEntityDescription(
            key="UV",
            name="UV Index",
        ),
        _div10("UV"),
    ),
    (
        SensorEntityDescription(
            key="C02",
            name="CO2",
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        ),
        _raw("C02"),
    ),
    (
        SensorEntityDescription(
            key="PM25",
            name="PM2.5",
            native_unit_of_measurement="µg/m³",
        ),
        _div10("PM25"),
    ),
    (
        SensorEntityDescription(
            key="PM100",
            name="PM10",
            native_unit_of_measurement="µg/m³",
        ),
        _div10("PM100"),
    ),
    (
        SensorEntityDescription(
            key="AQI",
            name="Air Quality Index",
        ),
        _raw("AQI"),
    ),
    # Extra sensors ES1..ES4
    (
        SensorEntityDescription(
            key="ES1T",
            name="Extra Sensor 1 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("ES1T"),
    ),
    (
        SensorEntityDescription(
            key="ES1H",
            name="Extra Sensor 1 Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("ES1H"),
    ),
    (
        SensorEntityDescription(
            key="ES2T",
            name="Extra Sensor 2 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("ES2T"),
    ),
    (
        SensorEntityDescription(
            key="ES2H",
            name="Extra Sensor 2 Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("ES2H"),
    ),
    (
        SensorEntityDescription(
            key="ES3T",
            name="Extra Sensor 3 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("ES3T"),
    ),
    (
        SensorEntityDescription(
            key="ES3H",
            name="Extra Sensor 3 Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("ES3H"),
    ),
    (
        SensorEntityDescription(
            key="ES4T",
            name="Extra Sensor 4 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("ES4T"),
    ),
    (
        SensorEntityDescription(
            key="ES4H",
            name="Extra Sensor 4 Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("ES4H"),
    ),
    # Soil sensors
    (
        SensorEntityDescription(
            key="So1T",
            name="Soil 1 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("So1T"),
    ),
    (
        SensorEntityDescription(
            key="So1M",
            name="Soil 1 Moisture",
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("So1M"),
    ),
    (
        SensorEntityDescription(
            key="So2T",
            name="Soil 2 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("So2T"),
    ),
    (
        SensorEntityDescription(
            key="So2M",
            name="Soil 2 Moisture",
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("So2M"),
    ),
)


# ---------------------------
# WeatherDisplay sensors
# ---------------------------

SENSORS_WEATHERDISPLAY: tuple[tuple[SensorEntityDescription, WDValue], ...] = (
    (
        SensorEntityDescription(
            key="T",
            name="Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        _div10("T"),
    ),
    (
        SensorEntityDescription(
            key="H",
            name="Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        _div10("H"),
    ),
    (
        SensorEntityDescription(
            key="TID",
            name="Transmitter ID",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        _raw("TID"),
    ),
)


# ---------------------------
# Setup
# ---------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WeatherDuinoCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    if _looks_like_weatherdisplay(data):
        sensor_set = SENSORS_WEATHERDISPLAY
        tid = _get_tid(data)
    else:
        sensor_set = SENSORS_4PRO
        tid = None

    entities: list[WeatherDuinoSensor] = []
    for description, wd_value in sensor_set:
        # Create only sensors that exist in the current JSON payload
        if wd_value.key in data:
            entities.append(
                WeatherDuinoSensor(
                    coordinator=coordinator,
                    entry=entry,
                    description=description,
                    wd_value=wd_value,
                    tid=tid,
                )
            )

    async_add_entities(entities)


class WeatherDuinoSensor(CoordinatorEntity[WeatherDuinoCoordinator], SensorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True  # "<device name> <entity name>"

    def __init__(
        self,
        coordinator: WeatherDuinoCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        wd_value: WDValue,
        tid: int | None,
    ) -> None:
        super().__init__(coordinator)

        self.entity_description = description
        self._wd_value = wd_value
        self._entry = entry
        self._tid = tid

        # CLEAN sensor name: no TID in the displayed name
        self._attr_name = description.name

        # Unique ID: include TID for WeatherDisplay so multiple transmitters can coexist
        if self._tid is not None:
            self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_tid{self._tid}_{description.key}"
        else:
            self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self._wd_value.value_fn(self.coordinator.data or {})

    @property
    def device_info(self) -> dict[str, Any]:
        dev_name = self.coordinator.device_id or self._entry.title

        if self.coordinator.wd_config.port and self.coordinator.wd_config.port != 80:
            cfg_url = f"http://{self.coordinator.wd_config.host}:{self.coordinator.wd_config.port}"
        else:
            cfg_url = f"http://{self.coordinator.wd_config.host}"

        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": dev_name,
            "manufacturer": "WeatherDuino",
            "model": "WeatherDuino (Local JSON)",
            "configuration_url": cfg_url,
        }
