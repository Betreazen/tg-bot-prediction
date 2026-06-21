"""Tests for timezone helpers."""

from bot.utils.timezone import tz_label, get_tz


def test_tz_label_includes_name_and_offset():
    label = tz_label()
    assert "Europe/Moscow" in label
    # Moscow is UTC+3 year round.
    assert "GMT+3" in label


def test_get_tz_is_cached():
    assert get_tz() is get_tz()
