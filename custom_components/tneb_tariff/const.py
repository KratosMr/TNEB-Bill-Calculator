"""Constants for the TNEB Tariff Calculator integration."""

DOMAIN = "tneb_tariff"

CONF_NAME = "name"
CONF_SOURCE_SENSOR = "source_sensor"
CONF_INITIAL_DATE = "initial_reading_date"
CONF_INITIAL_VALUE = "initial_reading_value"
CONF_CYCLE_MONTHS = "cycle_months"
CONF_FIXED_CHARGE = "fixed_charge"

DEFAULT_NAME = "TNEB Bill"
DEFAULT_CYCLE_MONTHS = 2
DEFAULT_FIXED_CHARGE = 0.0

ATTR_CYCLE_START = "cycle_start"
ATTR_NEXT_RESET = "next_reset"
ATTR_BASELINE_READING = "baseline_reading"
ATTR_APPROXIMATE_BASELINE = "approximate_baseline"
ATTR_UNITS_CONSUMED = "units_consumed"
ATTR_TARIFF_TABLE = "tariff_table_used"
ATTR_ENERGY_CHARGE = "energy_charge"
ATTR_FIXED_CHARGE = "fixed_charge"
ATTR_SLAB_BREAKDOWN = "slab_breakdown"
