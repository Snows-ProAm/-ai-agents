import pytest

from shared import config


def test_get_settings_requires_supabase_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    with pytest.raises(RuntimeError, match="SUPABASE_URL, SUPABASE_ANON_KEY"):
        config.get_settings()


def test_get_settings_loads_supabase_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    settings = config.get_settings()

    assert settings.supabase_url == "https://example.supabase.co"
    assert settings.supabase_anon_key == "anon-key"
