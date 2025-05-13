# TNEB Bill Calculator – Home Assistant Integration

This custom integration for Home Assistant thet calculates your TNEB electricity bill in real-time based on energy usage over a rolling 60-day period.

## 🔧 Features

- ⏱ Rolling 60-day billing cycle  
- ⚡ Tracks total electricity usage (kWh)  
- 💵 Calculates electricity bill using slab-based rates  
- 🧠 Smart persistent storage  
- ⚙️ UI-based configuration (no YAML!)  
- 📊 Exposes two sensors:  
  - `sensor.electricity_bill_60_days`  
  - `sensor.electricity_usage_60_days`

## 🛠 HACS Compatibility

This integration is compatible with HACS. Add it as a custom repository under the **Integrations** category.

## 📦 Manual Installation

1. Download or clone this repository.  
2. Copy the folder to your Home Assistant configuration:  
   ```
   config/custom_components/tneb_bill_calculator/
   ```
3. Restart Home Assistant.  
4. Go to **Settings → Devices & Services → + Add Integration**  
5. Search for **TNEB Bill Calculator**  
6. Choose:  
   - Your daily energy usage sensor (e.g. `sensor.vue2_total_daily_energy`)  
   - The **start date** of the 60-day billing period  

## 🧮 Billing Logic

### Slab Rates (up to 500 units):

| Units        | Rate (₹/unit) |
|--------------|---------------|
| 1 - 100      | 0.00          |
| 101 - 200    | 2.35          |
| 201 - 400    | 4.70          |
| 401 - 500    | 6.30          |

### Slab Rates (above 500 units):

| Units        | Rate (₹/unit) |
|--------------|---------------|
| 501 - 600    | 8.40          |
| 601 - 800    | 9.45          |
| 801 - 1000   | 10.50         |
| 1001+        | 11.55         |

## 🧠 Data Storage

Historical data is persisted locally in `.storage` and updated daily. The system keeps the latest 60 days of consumption and recalculates the bill every hour.

## 🛠 HACS Compatibility

This integration is compatible with HACS. Add it as a custom repository under the **Integrations** category.

