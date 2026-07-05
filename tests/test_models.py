"""Tests for Pydantic domain models."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models import AppState, GenerateForm, Settings


def test_settings_parses_example_json():
    settings = Settings.model_validate(
        {
            "invoice_amount_eur": 5000,
            "usdt_wallet": "TTestWallet",
            "from": {"name": "Ramin", "email": "r@example.com", "location": "Mashad"},
            "billed_to": {"name": "Boris", "company": "Initiative", "location": "France"},
        }
    )
    assert settings.from_party.name == "Ramin"
    assert settings.invoice_amount_eur == 5000


def test_app_state_parses_example_json():
    state = AppState.model_validate(
        {
            "last_invoice_number": 2334974,
            "vacation": {"used_this_year": 6, "carried_over": 7, "remaining": 31},
            "year": 2026,
            "history": [],
        }
    )
    assert state.last_invoice_number == 2334974
    assert state.vacation.remaining == 31


def test_generate_form_rejects_invalid_month():
    with pytest.raises(ValidationError):
        GenerateForm(year=2026, month=13)


def test_settings_rejects_negative_amount():
    with pytest.raises(ValidationError):
        Settings(invoice_amount_eur=-1, usdt_wallet="T", from_party={"name": "A"}, billed_to={"name": "B"})


def test_generate_form_accepts_off_days():
    form = GenerateForm(year=2026, month=7, off_days=[date(2026, 7, 3)])
    assert form.off_days == [date(2026, 7, 3)]
