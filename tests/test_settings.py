"""Tests for configuration parsing."""

from bot.config.settings import Settings


def _settings() -> Settings:
    # Reads the dummy env vars set in conftest.py.
    return Settings()


def test_admin_ids_parsed_and_trimmed():
    s = _settings()
    assert s.admin_ids_list == [111, 222, 333]


def test_admin_ids_empty_returns_empty_list(monkeypatch):
    monkeypatch.setenv("ADMIN_IDS", "")
    s = Settings()
    assert s.admin_ids_list == []


def test_database_urls_use_correct_drivers():
    s = _settings()
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.database_url_sync.startswith("postgresql://")
    assert s.db_name in s.database_url


def test_database_password_with_reserved_characters(monkeypatch):
    from sqlalchemy.engine import make_url

    password = "test@host:/?#%secret"
    monkeypatch.setenv("DB_PASSWORD", password)
    s = _settings()
    for value in (s.database_url, s.database_url_sync):
        parsed = make_url(value)
        assert parsed.password == password
        assert parsed.host == s.db_host
