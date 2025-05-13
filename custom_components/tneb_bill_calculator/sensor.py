from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        ElectricityBillSensor(coordinator, entry.entry_id, "bill"),
        ElectricityBillSensor(coordinator, entry.entry_id, "units"),
    ])

class ElectricityBillSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id, sensor_type):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._sensor_type = sensor_type
        self._attr_name = "Electricity Bill (₹)" if sensor_type == "bill" else "Electricity Usage (kWh)"
        self._attr_unique_id = f"{entry_id}_{sensor_type}"

    @property
    def state(self):
        return self.coordinator.data.get(self._sensor_type, 0)

    @property
    def unit_of_measurement(self):
        return "₹" if self._sensor_type == "bill" else "kWh"
