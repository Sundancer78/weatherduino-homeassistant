# custom_components/weatherduino/sensor.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
    UnitOfVolume,
    UnitOfElectricPotential,
    UnitOfTime,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WeatherDuinoCoordinator


@dataclass(frozen=True)
class WDValue:
    key: str
    value_fn: Callable[[dict[str, Any]], Any]


def _val(key: str) -> WDValue:
    return WDValue(key=key, value_fn=lambda data: data.get(key))


# NOTE:
# WeatherDuino sends scaled integers for many values (e.g. Tin=210 => 21.0°C)
# We keep those conversions here to produce proper units in HA.
SENSORS: tuple[tuple[SensorEntityDescription, WDValue], ...] = (
    (
        SensorEntityDescription(
            key="Tin",
            name="Inside Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        WDValue("Tin", lambda d: (d.get("Tin") / 10.0) if d.get("Tin") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="Hin",
            name="Inside Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        WDValue("Hin", lambda d: (d.get("Hin") / 10.0) if d.get("Hin") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="Tout",
            name="Outside Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        WDValue("Tout", lambda d: (d.get("Tout") / 10.0) if d.get("Tout") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="Hout",
            name="Outside Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        WDValue("Hout", lambda d: (d.get("Hout") / 10.0) if d.get("Hout") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="P",
            name="Pressure",
            device_class=SensorDeviceClass.PRESSURE,
            native_unit_of_measurement=UnitOfPressure.HPA,
        ),
        WDValue("P", lambda d: (d.get("P") / 10.0) if d.get("P") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="Wsp",
            name="Wind Speed",
            device_class=SensorDeviceClass.WIND_SPEED,
            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        ),
        WDValue("Wsp", lambda d: (d.get("Wsp") / 10.0) if d.get("Wsp") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="Wgs",
            name="Wind Gust",
            device_class=SensorDeviceClass.WIND_SPEED,
            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        ),
        WDValue("Wgs", lambda d: (d.get("Wgs") / 10.0) if d.get("Wgs") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="Wdir",
            name="Wind Direction",
            native_unit_of_measurement="°",
        ),
        _val("Wdir"),
    ),
    (
        SensorEntityDescription(
            key="Rtd",
            name="Rain Today",
            native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        ),
        WDValue("Rtd", lambda d: (d.get("Rtd") / 10.0) if d.get("Rtd") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="Rfr",
            name="Rain Rate",
            native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        ),
        WDValue("Rfr", lambda d: (d.get("Rfr") / 10.0) if d.get("Rfr") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="SR",
            name="Solar Radiation",
            device_class=SensorDeviceClass.IRRADIANCE,
            native_unit_of_measurement="W/m²",
        ),
        _val("SR"),
    ),
    (
        SensorEntityDescription(
            key="UV",
            name="UV Index",
            # In HA 2026.x there is no SensorDeviceClass.UV_INDEX, so keep it generic.
            # device_class intentionally omitted
            native_unit_of_measurement=None,
        ),
        WDValue("UV", lambda d: (d.get("UV") / 10.0) if d.get("UV") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="C02",
            name="CO2",
            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        ),
        _val("C02"),
    ),
    (
        SensorEntityDescription(
            key="PM25",
            name="PM2.5",
            native_unit_of_measurement="µg/m³",
        ),
        WDValue("PM25", lambda d: (d.get("PM25") / 10.0) if d.get("PM25") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="PM100",
            name="PM10",
            native_unit_of_measurement="µg/m³",
        ),
        WDValue("PM100", lambda d: (d.get("PM100") / 10.0) if d.get("PM100") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="AQI",
            name="Air Quality Index",
            native_unit_of_measurement=None,
        ),
        _val("AQI"),
    ),
    # Extra Sensors (ES1..ES4) are typically already scaled for your current config;
    # in your example they look like scaled ints (e.g. ES4T=212 => 21.2°C)
    (
        SensorEntityDescription(
            key="ES1T",
            name="Extra Sensor 1 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        WDValue("ES1T", lambda d: (d.get("ES1T") / 10.0) if d.get("ES1T") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="ES1H",
            name="Extra Sensor 1 Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        WDValue("ES1H", lambda d: (d.get("ES1H") / 10.0) if d.get("ES1H") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="ES2T",
            name="Extra Sensor 2 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        WDValue("ES2T", lambda d: (d.get("ES2T") / 10.0) if d.get("ES2T") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="ES2H",
            name="Extra Sensor 2 Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        WDValue("ES2H", lambda d: (d.get("ES2H") / 10.0) if d.get("ES2H") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="ES3T",
            name="Extra Sensor 3 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        WDValue("ES3T", lambda d: (d.get("ES3T") / 10.0) if d.get("ES3T") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="ES3H",
            name="Extra Sensor 3 Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        WDValue("ES3H", lambda d: (d.get("ES3H") / 10.0) if d.get("ES3H") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="ES4T",
            name="Extra Sensor 4 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        WDValue("ES4T", lambda d: (d.get("ES4T") / 10.0) if d.get("ES4T") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="ES4H",
            name="Extra Sensor 4 Humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        WDValue("ES4H", lambda d: (d.get("ES4H") / 10.0) if d.get("ES4H") is not None else None),
    ),
    # Soil
    (
        SensorEntityDescription(
            key="So1T",
            name="Soil 1 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        WDValue("So1T", lambda d: (d.get("So1T") / 10.0) if d.get("So1T") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="So1M",
            name="Soil 1 Moisture",
            native_unit_of_measurement=PERCENTAGE,
        ),
        WDValue("So1M", lambda d: (d.get("So1M") / 10.0) if d.get("So1M") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="So2T",
            name="Soil 2 Temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        WDValue("So2T", lambda d: (d.get("So2T") / 10.0) if d.get("So2T") is not None else None),
    ),
    (
        SensorEntityDescription(
            key="So2M",
            name="Soil 2 Moisture",
            native_unit_of_measurement=PERCENTAGE,
        ),
        WDValue("So2M", lambda d: (d.get("So2M") / 10.0) if d.get("So2M") is not None else None),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WeatherDuinoCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[WeatherDuinoSensor] = [
        WeatherDuinoSensor(coordinator, entry, description, wd_value) for description, wd_value in SENSORS
    ]
    async_add_entities(entities)


class WeatherDuinoSensor(CoordinatorEntity[WeatherDuinoCoordinator], SensorEntity):
    """WeatherDuino sensor entity."""

    _attr_should_poll = False
    _attr_has_entity_name = True  # => UI shows "<device name> <entity name>"

    def __init__(
        self,
        coordinator: WeatherDuinoCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        wd_value: WDValue,
    ) -> None:
        super().__init__(coordinator)

        self.entity_description = description
        self._wd_value = wd_value
        self._entry = entry

        # IMPORTANT FIX:
        # Do NOT prefix entity name with "WeatherDuino" or IP.
        # Entity name should be only the sensor label; device name comes from device registry.
        self._attr_name = description.name

        # Unique ID must stay stable and include the data key
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data or {}
        return self._wd_value.value_fn(data)

    @property
    def device_info(self) -> dict[str, Any]:
        # Use device-reported ID (RX-WeatherDuino-4Pro) as device name. This removes IP from the UI prefix.
        dev_name = self.coordinator.device_id or (self._entry.unique_id or self._entry.title)

        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": dev_name,
            "manufacturer": "WeatherDuino",
            "model": "WeatherDuino (Local JSON)",
            "configuration_url": f"http://{self.coordinator.wd_config.host}",
        }
