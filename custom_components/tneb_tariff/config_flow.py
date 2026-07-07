"""Config flow for TNEB Tariff Calculator."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_CYCLE_MONTHS,
    CONF_FIXED_CHARGE,
    CONF_INITIAL_DATE,
    CONF_INITIAL_VALUE,
    CONF_NAME,
    CONF_SOURCE_SENSOR,
    DEFAULT_CYCLE_MONTHS,
    DEFAULT_FIXED_CHARGE,
    DEFAULT_NAME,
    DOMAIN,
)


class TnebTariffConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TNEB Tariff Calculator."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_SOURCE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_INITIAL_DATE): selector.DateSelector(),
                vol.Optional(CONF_INITIAL_VALUE): vol.Coerce(float),
                vol.Required(
                    CONF_CYCLE_MONTHS, default=DEFAULT_CYCLE_MONTHS
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
                vol.Optional(
                    CONF_FIXED_CHARGE, default=DEFAULT_FIXED_CHARGE
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return TnebTariffOptionsFlow(config_entry)


class TnebTariffOptionsFlow(config_entries.OptionsFlow):
    """Allow changing settings after setup.

    Note: changing the initial reading date/value here only affects a
    fresh cycle calculation if you also clear the entities' restored
    state (e.g. by removing and re-adding the integration). Ongoing
    cycle tracking, once started, continues from its own stored
    baseline/cycle_start - it does not re-read these values every
    restart.
    """

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SOURCE_SENSOR,
                    default=current.get(CONF_SOURCE_SENSOR),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_CYCLE_MONTHS,
                    default=current.get(CONF_CYCLE_MONTHS, DEFAULT_CYCLE_MONTHS),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
                vol.Optional(
                    CONF_FIXED_CHARGE,
                    default=current.get(CONF_FIXED_CHARGE, DEFAULT_FIXED_CHARGE),
                ): vol.Coerce(float),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
