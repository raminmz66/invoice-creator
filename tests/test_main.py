"""Smoke tests for FastAPI routes."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.models import AppState, InvoiceHistoryEntry, PartyInfo, Settings, VacationState
from app.storage import save_settings, save_state


@pytest.fixture
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setattr("app.storage.DATA_DIR", tmp_path)
    monkeypatch.setattr("app.storage.SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr("app.storage.STATE_PATH", tmp_path / "state.json")
    return tmp_path


@pytest.fixture
def client(isolated_data):
    from app.main import app

    return TestClient(app)


@pytest.fixture
def seeded_data(isolated_data):
    settings = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TTestWallet123",
        from_party=PartyInfo(
            name="Ramin Maazallahi",
            email="r.mazallahi-ext@initiative-crm.com",
            location="Mashad, Iran",
        ),
        billed_to=PartyInfo(
            name="Boris Clement",
            company="Initiative solutions",
            location="Valreas, France",
        ),
        annual_vacation_entitlement=31,
    )
    state = AppState(
        last_invoice_number=2334974,
        vacation=VacationState(used_this_year=6, carried_over=7, remaining=32),
        year=2026,
        history=[],
    )
    save_settings(settings)
    save_state(state)
    return settings, state


def test_root_redirects_to_generate(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/generate"


def test_generate_empty_state_shows_setup_prompt(client):
    response = client.get("/generate")
    assert response.status_code == 200
    assert "Set up your invoice details first" in response.text


def test_settings_get_renders_form(client):
    response = client.get("/settings")
    assert response.status_code == 200
    assert "Invoice details" in response.text
    assert "chrome-card" in response.text
    assert "/static/settings.js" in response.text


def test_settings_post_saves_and_preserves_history(client, seeded_data):
    _, state = seeded_data
    state.history = [
        InvoiceHistoryEntry(
            invoice_number=1,
            date=date(2026, 1, 31),
            off_days=[],
            pdf_filename="test.pdf",
        )
    ]
    save_state(state)

    response = client.post(
        "/settings",
        data={
            "invoice_amount_eur": "5500",
            "usdt_wallet": "TUpdatedWallet",
            "from_name": "Ramin Maazallahi",
            "from_email": "r.mazallahi-ext@initiative-crm.com",
            "from_location": "Mashad, Iran",
            "billed_to_name": "Boris Clement",
            "billed_to_company": "Initiative solutions",
            "billed_to_location": "Valreas, France",
            "annual_vacation_entitlement": "31",
            "carried_over": "7",
            "used_this_year": "6",
            "last_invoice_number": "2334974",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/settings?saved=1"

    from app.storage import load_settings, load_state

    settings = load_settings()
    saved_state = load_state()
    assert settings is not None
    assert settings.invoice_amount_eur == 5500
    assert saved_state is not None
    assert len(saved_state.history) == 1


def test_generate_shows_year_rollover_banner(client, seeded_data):
    _, state = seeded_data
    state.year = 2025
    save_state(state)

    response = client.get("/generate?month=2026-01")
    assert response.status_code == 200
    assert "New year detected" in response.text
    assert 'name="rollover_carried_over"' in response.text
    assert "disabled" in response.text


def test_apply_rollover_resets_vacation(client, seeded_data):
    settings, state = seeded_data
    state.year = 2025
    save_state(state)

    response = client.post(
        "/generate",
        data={
            "month": "2026-01",
            "action": "apply_rollover",
            "rollover_reset": "1",
            "rollover_carried_over": "32",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/generate?month=2026-01"

    from app.storage import load_state

    updated = load_state()
    assert updated is not None
    assert updated.year == 2026
    assert updated.vacation.used_this_year == 0
    assert updated.vacation.carried_over == 32


def test_generate_blocks_until_rollover_applied(client, seeded_data):
    _, state = seeded_data
    state.year = 2025
    save_state(state)

    response = client.post(
        "/generate",
        data={"month": "2026-01", "action": "download"},
    )
    assert response.status_code == 400
    assert "New year detected" in response.text


def test_generate_with_settings_renders_paper_preview(client, seeded_data):
    response = client.get("/generate?month=2026-07")
    assert response.status_code == 200
    assert "invoice-document" in response.text
    assert "parties-table" in response.text
    assert "items-header" in response.text
    assert "Payment for July 2026" in response.text
    assert "Professional services" not in response.text
    assert "invoice-editor" in response.text
    assert "chrome-input" in response.text
    assert "2334975" in response.text
    assert "/static/generate.js" in response.text


def test_generate_preview_returns_pdf(client, seeded_data):
    response = client.post(
        "/generate",
        data={"month": "2026-07", "action": "preview"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_generate_download_updates_state(client, seeded_data):
    response = client.post(
        "/generate",
        data={"month": "2026-07", "action": "download"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    from app.storage import load_state

    state = load_state()
    assert state is not None
    assert state.last_invoice_number == 2334975
    assert len(state.history) == 1
