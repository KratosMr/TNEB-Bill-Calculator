# TNEB Tariff Calculator

A Home Assistant custom integration that calculates your electricity bill
using TNEB's (Tamil Nadu Electricity Board) telescopic slab tariff.

TNEB's domestic tariff isn't one continuous slab table - the whole table
that applies depends on your total units consumed in the billing cycle:

- **≤ 500 units** → one slab table
- **501-2000 units** → a different, wider slab table applied to the entire
  consumption

This integration:

- Tracks a billing cycle anchored to a real meter-reading date you provide
  (not a fixed calendar day), so it lines up with your actual TNEB cycle
- Computes units consumed since the start of the current cycle from your
  raw cumulative energy sensor
- Applies the correct TNEB slab table telescopically and gives you a live
  estimated bill, with a full slab-by-slab cost breakdown as an attribute

## Installation (HACS)

1. In Home Assistant, go to **HACS → Integrations → ⋮ (top right) → Custom
   repositories**
2. Add this repository's URL, category **Integration**
3. Find "TNEB Tariff Calculator" in HACS and install it
4. Restart Home Assistant

## Installation (manual)

Copy `custom_components/tneb_tariff` into your Home Assistant
`config/custom_components/` folder and restart.

## Setup

Settings → Devices & Services → Add Integration → **TNEB Tariff
Calculator**, then provide:

| Field | What to enter |
|---|---|
| Raw energy sensor | Your always-increasing cumulative kWh sensor |
| Date of the initial meter reading | The date you physically read your meter (ideally your last real bill's start date) |
| Meter reading on that date | The kWh value at that date (optional - leave blank to start counting from today) |
| Billing cycle length | 2 for bimonthly (TNEB's usual cycle) |
| Fixed charge | Optional flat charge added on top |

## Entities created

- `sensor.<name>_units_this_cycle` - units consumed since the current
  cycle started, with `cycle_start`, `next_reset`, and `baseline_reading`
  attributes
- `sensor.<name>` - the calculated bill, with `units_consumed`,
  `energy_charge`, `tariff_table_used`, and `slab_breakdown` attributes

## Notes / limitations

- Only the energy-charge slabs you supply are modeled (0-2000 units from
  TNEB's published table). Consumption beyond 2000 units is billed at the
  highest known rate as a fallback - update `tariff.py` if TNEB publishes
  higher slabs.
- If your anchor date is more than one billing cycle in the past when you
  set this up, the integration can't retroactively know your meter's
  reading at the true cycle start, so it starts counting from the live
  reading instead and marks `approximate_baseline: true` on the units
  sensor until the next cycle boundary.
- Fixed/service charges based on connected load aren't modeled beyond the
  flat optional `fixed_charge` field.
