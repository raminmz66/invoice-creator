"""Tests for JSON storage layer."""

import pytest

from app.models import AppState, PartyInfo, Settings, VacationState
from app.storage import load_settings, load_state, save_settings, save_state


@pytest.fixture
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setattr("app.storage.DATA_DIR", tmp_path)
    monkeypatch.setattr("app.storage.SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr("app.storage.STATE_PATH", tmp_path / "state.json")
    return tmp_path


def test_save_and_load_settings(isolated_data):
    settings = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TTest123",
        from_party=PartyInfo(name="Ramin", location="Mashad"),
        billed_to=PartyInfo(name="Boris", company="Initiative"),
    )
    save_settings(settings)
    loaded = load_settings()
    assert loaded is not None
    assert loaded.invoice_amount_eur == 5000
    assert loaded.usdt_wallet == "TTest123"
    assert loaded.from_party.name == "Ramin"


def test_load_settings_missing_returns_none(isolated_data):
    assert load_settings() is None


def test_save_and_load_state(isolated_data):
    state = AppState(
        last_invoice_number=100,
        vacation=VacationState(used_this_year=2, carried_over=5, remaining=34),
        year=2026,
    )
    save_state(state)
    loaded = load_state()
    assert loaded is not None
    assert loaded.last_invoice_number == 100
    assert loaded.vacation.remaining == 34


def test_settings_json_uses_from_alias(isolated_data):
    settings = Settings(
        invoice_amount_eur=100,
        usdt_wallet="T",
        from_party=PartyInfo(name="Sender"),
        billed_to=PartyInfo(name="Client"),
    )
    save_settings(settings)
    raw = (isolated_data / "settings.json").read_text(encoding="utf-8")
    assert '"from"' in raw
    assert "from_party" not in raw
