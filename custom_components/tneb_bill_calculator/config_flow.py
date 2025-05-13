from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers.selector import selector
from homeassistant.const import CONF_NAME
from .const import DOMAIN, CONF_SENSOR, CONF_START_DATE

class ElectricityBillFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="TNEB Bill Calculator", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_SENSOR): selector({"entity": {"domain": "sensor"}}),
                vol.Required(CONF_START_DATE): selector({"date": {}})
            }),
        )
