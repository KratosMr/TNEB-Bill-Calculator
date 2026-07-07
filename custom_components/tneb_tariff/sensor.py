"""Sensor platform for TNEB Tariff Calculator.

Two entities are created:

* TnebUnitsSensor  - "Units This Cycle". Owns all the cycle-tracking state:
  the anchor/baseline meter reading, the current cycle's start date, and
  the next reset date. It listens to your raw cumulative energy sensor
  (kWh, always-increasing) and reports units consumed since the current
  cycle's baseline.

* TnebBillSensor - "Bill". Purely derived: it reads TnebUnitsSensor's
  current value directly (via an in-memory callback, not through the HA
  state machine) and applies the TNEB telescopic slab tariff.

Cycle boundaries are computed from a user-supplied anchor date (the date
you took an actual meter reading) plus a cycle length in months (2 for
TNEB's bimonthly billing). Every future boundary is derived from that
anchor, not from calendar month/2-month HA defaults - so it lines up with
your real billing dates.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_state_change_event,
)
from homeassistant.helpers.restore_state import RestoreEntity
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_APPROXIMATE_BASELINE,
    ATTR_BASELINE_READING,
    ATTR_CYCLE_START,
    ATTR_ENERGY_CHARGE,
    ATTR_FIXED_CHARGE,
    ATTR_NEXT_RESET,
    ATTR_SLAB_BREAKDOWN,
    ATTR_TARIFF_TABLE,
    ATTR_UNITS_CONSUMED,
    CONF_CYCLE_MONTHS,
    CONF_FIXED_CHARGE,
    CONF_INITIAL_DATE,
    CONF_INITIAL_VALUE,
    CONF_NAME,
    CONF_SOURCE_SENSOR,
    DEFAULT_CYCLE_MONTHS,
    DEFAULT_FIXED_CHARGE,
    DEFAULT_NAME,
)
from .cycle_util import add_months
from .tariff import calculate_energy_charge


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = {**entry.data, **entry.options}
    name = data.get(CONF_NAME, DEFAULT_NAME)
    source_sensor = data[CONF_SOURCE_SENSOR]
    cycle_months = data.get(CONF_CYCLE_MONTHS, DEFAULT_CYCLE_MONTHS)
    fixed_charge = data.get(CONF_FIXED_CHARGE, DEFAULT_FIXED_CHARGE)

    initial_date_raw = data.get(CONF_INITIAL_DATE)
    initial_date = dt_util.parse_date(initial_date_raw) if initial_date_raw else dt_util.now().date()
    initial_value = data.get(CONF_INITIAL_VALUE)

    units_sensor = TnebUnitsSensor(
        entry.entry_id, name, source_sensor, initial_date, initial_value, cycle_months
    )
    bill_sensor = TnebBillSensor(entry.entry_id, name, units_sensor, fixed_charge)

    async_add_entities([units_sensor, bill_sensor])


class TnebUnitsSensor(RestoreEntity, SensorEntity):
    """Units consumed in the current TNEB billing cycle."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "kWh"
    _attr_icon = "mdi:meter-electric"
    _attr_should_poll = False

    def __init__(
        self,
        entry_id: str,
        name: str,
        source_sensor: str,
        initial_date: date,
        initial_value: float | None,
        cycle_months: int,
    ) -> None:
        self._entry_id = entry_id
        self._source_sensor = source_sensor
        self._initial_date = initial_date
        self._initial_value = initial_value
        self._cycle_months = cycle_months

        self._attr_name = f"{name} Units This Cycle"
        self._attr_unique_id = f"{entry_id}_units"
        self._attr_native_value = None
        self._attr_extra_state_attributes: dict = {}

        self._baseline_reading: float | None = None
        self._cycle_start: date | None = None
        self._next_reset: date | None = None
        self._approximate_baseline = False
        self._unsub_reset: Callable | None = None
        self._listeners: list[Callable[[], None]] = []

    # -- external hook used by TnebBillSensor --
    def add_listener(self, callback_fn: Callable[[], None]) -> None:
        self._listeners.append(callback_fn)

    def _notify_listeners(self) -> None:
        for cb in self._listeners:
            cb()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        restored = False
        last_state = await self.async_get_last_state()
        if last_state is not None:
            attrs = last_state.attributes
            if attrs.get(ATTR_CYCLE_START) and attrs.get(ATTR_BASELINE_READING) is not None:
                try:
                    self._cycle_start = dt_util.parse_date(attrs[ATTR_CYCLE_START])
                    self._next_reset = dt_util.parse_date(attrs[ATTR_NEXT_RESET])
                    self._baseline_reading = float(attrs[ATTR_BASELINE_READING])
                    self._approximate_baseline = bool(
                        attrs.get(ATTR_APPROXIMATE_BASELINE, False)
                    )
                    restored = True
                except (KeyError, ValueError, TypeError):
                    restored = False

        if not restored:
            self._initialize_cycle()

        self._schedule_next_reset()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._source_sensor], self._handle_source_update
            )
        )

        current = self.hass.states.get(self._source_sensor)
        if current is not None:
            self._recalculate(current.state)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_reset:
            self._unsub_reset()

    def _initialize_cycle(self) -> None:
        """Compute which cycle 'today' falls into, anchored to the configured date."""
        today = dt_util.now().date()
        cycle_start = self._initial_date
        next_reset = add_months(cycle_start, self._cycle_months)
        baseline = self._initial_value

        fast_forwarded = False
        while next_reset <= today:
            cycle_start = next_reset
            next_reset = add_months(cycle_start, self._cycle_months)
            fast_forwarded = True

        if fast_forwarded or baseline is None:
            # We don't have a real historical reading for this boundary
            # (either no initial value was given, or the anchor date is
            # more than one cycle in the past). Best effort: start
            # counting from whatever the source sensor reads right now.
            # This under-counts the current, already-in-progress cycle -
            # the count will be fully accurate starting next cycle.
            current = self.hass.states.get(self._source_sensor)
            try:
                baseline = float(current.state) if current else 0.0
            except (ValueError, TypeError):
                baseline = 0.0
            self._approximate_baseline = True
        else:
            self._approximate_baseline = False

        self._cycle_start = cycle_start
        self._next_reset = next_reset
        self._baseline_reading = baseline

    def _schedule_next_reset(self) -> None:
        if self._unsub_reset:
            self._unsub_reset()
        reset_dt = dt_util.as_local(
            datetime.combine(self._next_reset, time.min)
        )
        self._unsub_reset = async_track_point_in_time(
            self.hass, self._handle_cycle_reset, reset_dt
        )

    @callback
    def _handle_cycle_reset(self, now) -> None:
        current = self.hass.states.get(self._source_sensor)
        try:
            baseline = float(current.state) if current else self._baseline_reading
        except (ValueError, TypeError):
            baseline = self._baseline_reading

        self._cycle_start = self._next_reset
        self._next_reset = add_months(self._cycle_start, self._cycle_months)
        self._baseline_reading = baseline
        self._approximate_baseline = False

        self._schedule_next_reset()
        self._recalculate(current.state if current else None)
        self.async_write_ha_state()
        self._notify_listeners()

    @callback
    def _handle_source_update(self, event: Event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        self._recalculate(new_state.state)
        self.async_write_ha_state()
        self._notify_listeners()

    def _recalculate(self, raw_value) -> None:
        try:
            current_reading = float(raw_value)
        except (ValueError, TypeError):
            return
        if self._baseline_reading is None:
            return

        units = current_reading - self._baseline_reading
        if units < 0:
            # Source sensor reset (e.g. meter/device reboot) - re-baseline
            # from here so we don't report a negative or wildly wrong value.
            self._baseline_reading = current_reading
            units = 0.0

        self._attr_native_value = round(units, 3)
        self._attr_extra_state_attributes = {
            ATTR_CYCLE_START: self._cycle_start.isoformat(),
            ATTR_NEXT_RESET: self._next_reset.isoformat(),
            ATTR_BASELINE_READING: self._baseline_reading,
            ATTR_APPROXIMATE_BASELINE: self._approximate_baseline,
        }

    @property
    def native_value(self):
        return self._attr_native_value


class TnebBillSensor(SensorEntity):
    """Calculated TNEB bill for the current cycle, derived from TnebUnitsSensor."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "INR"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:currency-inr"
    _attr_should_poll = False

    def __init__(
        self, entry_id: str, name: str, units_sensor: TnebUnitsSensor, fixed_charge: float
    ) -> None:
        self._entry_id = entry_id
        self._units_sensor = units_sensor
        self._fixed_charge = fixed_charge
        self._attr_name = f"{name}"
        self._attr_unique_id = f"{entry_id}_bill"
        self._attr_native_value = None
        self._attr_extra_state_attributes: dict = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._units_sensor.add_listener(self._recalculate)
        self._recalculate()

    @callback
    def _recalculate(self) -> None:
        units = self._units_sensor.native_value
        result = calculate_energy_charge(units if units is not None else 0.0)
        total_bill = round(result["energy_charge"] + self._fixed_charge, 2)

        self._attr_native_value = total_bill
        self._attr_extra_state_attributes = {
            ATTR_UNITS_CONSUMED: units,
            ATTR_ENERGY_CHARGE: result["energy_charge"],
            ATTR_FIXED_CHARGE: self._fixed_charge,
            ATTR_TARIFF_TABLE: result["table_used"],
            ATTR_SLAB_BREAKDOWN: result["breakdown"],
            **self._units_sensor.extra_state_attributes,
        }
        if self.hass is not None:
            self.async_write_ha_state()
