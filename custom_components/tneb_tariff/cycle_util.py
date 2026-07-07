"""Small date helpers - avoids depending on dateutil being present."""

from __future__ import annotations

import calendar
from datetime import date


def add_months(d: date, months: int) -> date:
    """Return d shifted forward by `months` calendar months.

    Clamps the day to the last valid day of the resulting month
    (e.g. Jan 31 + 1 month -> Feb 28/29).
    """
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
