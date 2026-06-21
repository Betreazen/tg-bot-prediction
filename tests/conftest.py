"""Test configuration.

Settings are read from the environment at import time (and require BOT_TOKEN /
DB_PASSWORD), so we populate safe dummy values before any ``bot.*`` import.
"""

import os

os.environ.setdefault("BOT_TOKEN", "123456:test-token")
os.environ.setdefault("DB_PASSWORD", "test-password")
os.environ.setdefault("ADMIN_IDS", "111, 222 , 333")
os.environ.setdefault("SCHEDULER_TIMEZONE", "Europe/Moscow")
