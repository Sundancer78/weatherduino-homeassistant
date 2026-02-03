from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from ipaddress import ip_address, IPv4Address, IPv6Address
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import slugify
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import WeatherDuinoCoordinator


# ---------- helpers ----------

def _to_number(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


@dataclass(frozen=True)
class WDValue:
    key: str
    fn: Callable[[dict[str, Any]], Any]


def div10(key: str) -> WDValue:
    return WDValue(
        key,
        lambda d: (_to_number(d.get(key)) / 10) if _to_number(d.get(key)) is not None else None,
    )


def num(key: str) -> WDValue:
    return WDValue(key, lambda d: _to_number(d.get(key)))


def epoch(key: str) -> WDValue:
    return WDValue(
        key,
        lambda d: datetime.fromtimestamp(_to_number(d.get(key)), tz=timezone.utc)
        if _to_number(d.get(key)) is not None else None,
    )


def raw_int(key: str) -> WDValue:
    """Return numeric if possible and cast to int (e.g. for CO2, Wdir, TID)."""
    def _fn(d: dict[str, Any]) -> Any:
        n = _to_number(d.get(key))
        if n is None:
            return d.get(key)
        return int(round(n))
    return WDValue(key, _fn)


def ip_suffix(host: str) -> str:
    try:
        ip = ip_address(host)
    except ValueError:
        return slugify(host)

    if isinstance(ip, IPv4Address):
        parts = host.split(".")
        if len(parts) >= 2:
            return f"{parts[-2]}_{parts[-1]}"
        return slugify(host)

    if isinstance(ip, IPv6Address):
        exploded = ip.exploded.split(":")
        return "_".join(exploded[-4:])

    return slugify(host)


def aq_avgmode_value() -> WDValue:
    """
    AQM2: AVG_M is AQ_AVGMODE:
      1= 1 Hour Average
      2= 3 Hours Average
      3= Nowcast 12H
      4= 24 Hours Average
    """
    mapping = {
        1: "1 hour",
        2: "3 hours",
        3: "nowcast 12h",
        4: "24 hours",
    }

    def _fn(d: dict[str, Any]) -> Any:
        n = _to_number(d.get("AVG_M"))
        if n is None:
            return None
        code = int(round(n))
        return mapping.get(code, f"unknown ({code})")

    return WDValue("AVG_M", _fn)


# ---------- sensor definitions ----------

PREC2 = 2

SENSORS_4PRO = (
    (SensorEntityDescription(key="Tin", name="Inside Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("Tin")),
    (SensorEntityDescription(key="Hin", name="Inside Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("Hin")),
    (SensorEntityDescription(key="Tout", name="Outside Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("Tout")),
    (SensorEntityDescription(key="Hout", name="Outside Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("Hout")),
    (SensorEntityDescription(key="P", name="Pressure", device_class=SensorDeviceClass.PRESSURE, native_unit_of_measurement=UnitOfPressure.HPA, suggested_display_precision=PREC2), div10("P")),

    (SensorEntityDescription(key="Wsp", name="Wind Speed", device_class=SensorDeviceClass.WIND_SPEED, native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND, suggested_display_precision=PREC2), div10("Wsp")),
    (SensorEntityDescription(key="Wgs", name="Wind Gust", device_class=SensorDeviceClass.WIND_SPEED, native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND, suggested_display_precision=PREC2), div10("Wgs")),
    (SensorEntityDescription(key="Wdir", name="Wind Direction", native_unit_of_measurement="°", suggested_display_precision=0), raw_int("Wdir")),

    (SensorEntityDescription(key="Rtd", name="Rain Today", native_unit_of_measurement=UnitOfLength.MILLIMETERS, suggested_display_precision=PREC2), div10("Rtd")),
    (SensorEntityDescription(key="Rfr", name="Rain Rate", native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR, suggested_display_precision=PREC2), div10("Rfr")),

    (SensorEntityDescription(key="SR", name="Solar Radiation", device_class=SensorDeviceClass.IRRADIANCE, native_unit_of_measurement="W/m²", suggested_display_precision=0), raw_int("SR")),
    (SensorEntityDescription(key="UV", name="UV Index", suggested_display_precision=0), raw_int("UV")),

    (SensorEntityDescription(key="C02", name="CO2", native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION, suggested_display_precision=0), raw_int("C02")),
    (SensorEntityDescription(key="PM25", name="PM2.5", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM25")),
    (SensorEntityDescription(key="PM100", name="PM10", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM100")),
    (SensorEntityDescription(key="AQI", name="Air Quality Index", suggested_display_precision=0), raw_int("AQI")),

    (SensorEntityDescription(key="ES1T", name="Extra Sensor 1 Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("ES1T")),
    (SensorEntityDescription(key="ES1H", name="Extra Sensor 1 Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("ES1H")),
    (SensorEntityDescription(key="ES2T", name="Extra Sensor 2 Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("ES2T")),
    (SensorEntityDescription(key="ES2H", name="Extra Sensor 2 Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("ES2H")),
    (SensorEntityDescription(key="ES3T", name="Extra Sensor 3 Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("ES3T")),
    (SensorEntityDescription(key="ES3H", name="Extra Sensor 3 Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("ES3H")),
    (SensorEntityDescription(key="ES4T", name="Extra Sensor 4 Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("ES4T")),
    (SensorEntityDescription(key="ES4H", name="Extra Sensor 4 Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("ES4H")),

    (SensorEntityDescription(key="So1T", name="Soil 1 Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("So1T")),
    (SensorEntityDescription(key="So1M", name="Soil 1 Moisture", native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("So1M")),
    (SensorEntityDescription(key="So2T", name="Soil 2 Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("So2T")),
    (SensorEntityDescription(key="So2M", name="Soil 2 Moisture", native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("So2M")),

    (SensorEntityDescription(key="ts", name="Last Update", device_class=SensorDeviceClass.TIMESTAMP, entity_category=EntityCategory.DIAGNOSTIC), epoch("ts")),
    (SensorEntityDescription(key="TID", name="Device Type", entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=0), raw_int("TID")),
)

SENSORS_WEATHERDISPLAY = (
    (SensorEntityDescription(key="T", name="Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("T")),
    (SensorEntityDescription(key="H", name="Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("H")),
    (SensorEntityDescription(key="TID", name="Device Type", entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=0), raw_int("TID")),
)

SENSORS_AQM3 = (
    (SensorEntityDescription(key="T", name="Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("T")),
    (SensorEntityDescription(key="H", name="Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("H")),
    (SensorEntityDescription(key="P", name="Pressure", device_class=SensorDeviceClass.PRESSURE, native_unit_of_measurement=UnitOfPressure.HPA, suggested_display_precision=PREC2), div10("P")),

    (SensorEntityDescription(key="PM25_last", name="PM2.5 Last", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM25_last")),
    (SensorEntityDescription(key="PM100_last", name="PM10 Last", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM100_last")),
    (SensorEntityDescription(key="PM25_1H", name="PM2.5 1h", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM25_1H")),
    (SensorEntityDescription(key="PM100_1H", name="PM10 1h", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM100_1H")),
    (SensorEntityDescription(key="PM25_3H", name="PM2.5 3h", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM25_3H")),
    (SensorEntityDescription(key="PM100_3H", name="PM10 3h", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM100_3H")),
    (SensorEntityDescription(key="PM25_12H", name="PM2.5 12h", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM25_12H")),
    (SensorEntityDescription(key="PM100_12H", name="PM10 12h", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM100_12H")),
    (SensorEntityDescription(key="PM25_24H", name="PM2.5 24h", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM25_24H")),
    (SensorEntityDescription(key="PM100_24H", name="PM10 24h", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM100_24H")),

    (SensorEntityDescription(key="CO2", name="CO2", native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION, suggested_display_precision=0), raw_int("CO2")),

    (SensorEntityDescription(key="ts", name="Last Update", device_class=SensorDeviceClass.TIMESTAMP, entity_category=EntityCategory.DIAGNOSTIC), epoch("ts")),
    (SensorEntityDescription(key="TID", name="Device Type", entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=0), raw_int("TID")),
)

SENSORS_AQM2 = (
    (SensorEntityDescription(key="T", name="Temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, suggested_display_precision=PREC2), div10("T")),
    (SensorEntityDescription(key="H", name="Humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, suggested_display_precision=PREC2), div10("H")),

    (SensorEntityDescription(key="PM25", name="PM2.5", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM25")),
    (SensorEntityDescription(key="PM100", name="PM10", native_unit_of_measurement="µg/m³", suggested_display_precision=PREC2), div10("PM100")),

    (SensorEntityDescription(key="PM25AQI", name="PM2.5 AQI", entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=PREC2), div10("PM25AQI")),
    (SensorEntityDescription(key="PM100AQI", name="PM10 AQI", entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=PREC2), div10("PM100AQI")),

    # renamed + value mapped to text
    (SensorEntityDescription(key="AVG_M", name="AQ Average Mode", entity_category=EntityCategory.DIAGNOSTIC), aq_avgmode_value()),

    (SensorEntityDescription(key="CO2", name="CO2", native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION, suggested_display_precision=0), raw_int("CO2")),
    (SensorEntityDescription(key="TID", name="Device Type", entity_category=EntityCategory.DIAGNOSTIC, suggested_display_precision=0), raw_int("TID")),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: WeatherDuinoCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    dtype = getattr(coordinator, "device_type", "unknown")

    if dtype == "4pro":
        sensor_defs = SENSORS_4PRO
    elif dtype == "weatherdisplay":
        sensor_defs = SENSORS_WEATHERDISPLAY
    elif dtype == "aqm2":
        sensor_defs = SENSORS_AQM2
    elif dtype == "aqm3":
        sensor_defs = SENSORS_AQM3
    else:
        if "Tin" in data or "Wsp" in data:
            sensor_defs = SENSORS_4PRO
        elif "PM25_last" in data and "PM25_24H" in data:
            sensor_defs = SENSORS_AQM3
        elif "PM25AQI" in data and "AVG_M" in data:
            sensor_defs = SENSORS_AQM2
        elif "T" in data and "H" in data:
            sensor_defs = SENSORS_WEATHERDISPLAY
        else:
            sensor_defs = tuple()

    entities: list[WeatherDuinoSensor] = []
    for desc, wd in sensor_defs:
        if wd.key in data:
            entities.append(WeatherDuinoSensor(coordinator, desc, wd))

    async_add_entities(entities)


class WeatherDuinoSensor(CoordinatorEntity[WeatherDuinoCoordinator], SensorEntity):
    _attr_should_poll = False

    def __init__(self, coordinator: WeatherDuinoCoordinator, description: SensorEntityDescription, wd_value: WDValue) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._wd_value = wd_value

        suffix = ip_suffix(coordinator.host)
        self._attr_suggested_object_id = f"weatherduino_{slugify(description.name)}_wd{suffix}"
        self._attr_unique_id = f"{coordinator.host}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self._wd_value.fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        # add mode_code attribute for AQM2 AVG_M
        if self.entity_description.key == "AVG_M":
            code = _to_number((self.coordinator.data or {}).get("AVG_M"))
            if code is not None:
                return {"mode_code": int(round(code))}
        return None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.host)},
            name=self.coordinator.device_id,
            manufacturer="WeatherDuino",
            model=self.coordinator.device_model,
            configuration_url=self.coordinator.configuration_url,
        )
