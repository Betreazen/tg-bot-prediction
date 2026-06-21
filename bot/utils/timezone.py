"""Timezone helpers.

The application timezone is configured once via ``SCHEDULER_TIMEZONE``.
We cache the ``pytz`` object so handlers/services don't rebuild it on every
request, and expose a human-readable label so the UI never hard-codes "GMT+3".
"""

from datetime import datetime
from functools import lru_cache

import pytz

from bot.config.settings import settings


@lru_cache
def get_tz() -> pytz.BaseTzInfo:
    """Return the cached application timezone."""
    return pytz.timezone(settings.scheduler_timezone)


def now() -> datetime:
    """Return the current time in the application timezone."""
    return datetime.now(get_tz())


def tz_label() -> str:
    """Return a human-readable timezone label, e.g. ``Europe/Moscow (GMT+3)``."""
    offset = now().utcoffset()
    if offset is None:
        return settings.scheduler_timezone

    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    suffix = f"{sign}{hours}" + (f":{minutes:02d}" if minutes else "")
    return f"{settings.scheduler_timezone} (GMT{suffix})"
