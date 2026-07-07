"""TNEB telescopic tariff slab calculation.

TNEB domestic tariff does not use one continuous slab table. Instead, the
table that applies to the ENTIRE bill depends on which band the total units
consumed in the billing cycle falls into:

  * Total units <= 500   -> Table A (slabs 1-500)
  * Total units 501-2000 -> Table B (slabs 1-2000, wider bands, higher rates)

Within whichever table applies, the charge is telescopic: units are billed
slab by slab from unit 1 upward until all consumed units are accounted for.

Each table entry is (slab_width_in_units, rate_per_unit).
"""

from __future__ import annotations

TABLE_UP_TO_500 = [
    (100, 0.0),    # 1-100
    (100, 0.0),    # 101-200
    (200, 4.7),    # 201-400
    (100, 6.3),    # 401-500
]

TABLE_501_TO_2000 = [
    (100, 0.0),    # 1-100
    (300, 4.7),    # 101-400
    (100, 6.3),    # 401-500
    (100, 8.4),    # 501-600
    (200, 9.45),   # 601-800
    (200, 10.5),   # 801-1000
    (1000, 11.55), # 1001-2000
]


def get_tariff_table(units: float) -> tuple[str, list[tuple[float, float]]]:
    """Return (label, table) for the given total units in the cycle."""
    if units <= 500:
        return "up_to_500", TABLE_UP_TO_500
    return "501_to_2000", TABLE_501_TO_2000


def calculate_energy_charge(units: float) -> dict:
    """Calculate the telescopic energy charge for a given unit total.

    Returns a dict with the total charge, which table was used, and a
    slab-by-slab breakdown (useful as sensor attributes).
    """
    if units is None or units <= 0:
        return {
            "energy_charge": 0.0,
            "table_used": "none",
            "breakdown": [],
        }

    table_label, table = get_tariff_table(units)

    remaining = float(units)
    breakdown = []
    total_cost = 0.0
    slab_start = 1

    for slab_width, rate in table:
        if remaining <= 0:
            break
        consumed = min(remaining, slab_width)
        slab_cost = round(consumed * rate, 2)
        total_cost += slab_cost
        breakdown.append(
            {
                "from_unit": slab_start,
                "to_unit": slab_start + slab_width - 1,
                "units_billed": round(consumed, 2),
                "rate": rate,
                "cost": slab_cost,
            }
        )
        remaining -= consumed
        slab_start += slab_width

    # Safety net: if consumption exceeds the highest table we have (>2000),
    # bill the excess at the last known slab rate rather than silently
    # dropping it. Update TABLE_501_TO_2000 / add a new table if TNEB
    # publishes rates beyond 2000 units.
    if remaining > 0 and table:
        last_rate = table[-1][1]
        extra_cost = round(remaining * last_rate, 2)
        total_cost += extra_cost
        breakdown.append(
            {
                "from_unit": slab_start,
                "to_unit": slab_start + remaining - 1,
                "units_billed": round(remaining, 2),
                "rate": last_rate,
                "cost": extra_cost,
                "note": "beyond configured tariff tables - billed at last known rate",
            }
        )

    return {
        "energy_charge": round(total_cost, 2),
        "table_used": table_label,
        "breakdown": breakdown,
    }
