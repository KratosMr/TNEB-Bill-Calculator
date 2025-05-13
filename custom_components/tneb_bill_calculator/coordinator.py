from datetime import datetime, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import callback
from homeassistant.helpers.storage import Store
from .billing_logic import calculate_bill
from .const import DOMAIN, CONF_SENSOR, CONF_START_DATE

class BillCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, logger=hass.logger, name=DOMAIN, update_interval=timedelta(hours=1))
        self.hass = hass
        self.entry = entry
        self.usage = []
        self.sensor = entry.data[CONF_SENSOR]
        self.start_date = datetime.strptime(entry.data[CONF_START_DATE], "%Y-%m-%d")
        self.store = Store(hass, 1, f"{DOMAIN}_usage_{entry.entry_id}.json")

    async def async_config_entry_first_refresh(self):
        await self._load_usage()
        await self._update_data()

    async def _load_usage(self):
        saved = await self.store.async_load()
        if saved:
            self.usage = saved.get("usage", [])
            self.start_date = datetime.strptime(saved.get("start_date"), "%Y-%m-%d")

    async def _save_usage(self):
        await self.store.async_save({
            "usage": self.usage,
            "start_date": self.start_date.strftime("%Y-%m-%d")
        })

    async def _update_data(self):
        state = self.hass.states.get(self.sensor)
        if state is not None and state.state not in ("unknown", "unavailable"):
            try:
                today = datetime.now().date()
                if len(self.usage) > 0 and self.usage[-1]["date"] == str(today):
                    self.usage[-1]["value"] = float(state.state)
                else:
                    self.usage.append({"date": str(today), "value": float(state.state)})
                self.usage = self.usage[-60:]
                await self._save_usage()
            except Exception:
                pass

        total_units = sum(item["value"] for item in self.usage)
        return {
            "bill": calculate_bill(total_units),
            "units": round(total_units, 2)
        }
