"""Tests for invoice generation business logic."""

from datetime import date

from app.invoice_service import (
    apply_generation,
    build_draft,
    compute_remaining,
    last_day_of_month,
    pdf_filename,
    settings_complete,
    validate_generate,
)
from app.models import AppState, GenerateForm, InvoiceDraft, PartyInfo, Settings, VacationState


def test_last_day_of_month():
    assert last_day_of_month(2026, 6) == date(2026, 6, 30)
    assert last_day_of_month(2026, 2) == date(2026, 2, 28)


def test_compute_remaining():
    assert compute_remaining(carried_over=7, entitlement=31, used=6) == 32


def test_build_draft_increments_invoice_number():
    settings = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TWallet",
        from_party=PartyInfo(name="Ramin"),
        billed_to=PartyInfo(name="Boris"),
    )
    state = AppState(
        last_invoice_number=2334974,
        vacation=VacationState(used_this_year=6, carried_over=7, remaining=32),
        year=2026,
    )
    form = GenerateForm(year=2026, month=7, off_days=[date(2026, 7, 3)])
    draft = build_draft(settings, state, form)
    assert draft.invoice_number == 2334975
    assert draft.invoice_date == date(2026, 7, 31)
    assert draft.off_days == [date(2026, 7, 3)]


def test_validate_generate_rejects_too_many_off_days():
    settings = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TWallet",
        from_party=PartyInfo(name="Ramin"),
        billed_to=PartyInfo(name="Boris"),
    )
    state = AppState(
        last_invoice_number=1,
        vacation=VacationState(used_this_year=0, carried_over=0, remaining=1),
        year=2026,
    )
    form = GenerateForm(
        year=2026,
        month=7,
        off_days=[date(2026, 7, 1), date(2026, 7, 2)],
    )
    errors = validate_generate(settings, state, form)
    assert any("remaining" in error.lower() for error in errors)


def test_apply_generation_updates_state():
    settings = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TWallet",
        from_party=PartyInfo(name="Ramin"),
        billed_to=PartyInfo(name="Boris"),
        annual_vacation_entitlement=31,
    )
    state = AppState(
        last_invoice_number=100,
        vacation=VacationState(used_this_year=2, carried_over=5, remaining=34),
        year=2026,
    )
    form = GenerateForm(year=2026, month=7, off_days=[date(2026, 7, 10)])
    draft = build_draft(settings, state, form)
    new_state = apply_generation(state, draft, form)
    assert new_state.last_invoice_number == 101
    assert new_state.vacation.used_this_year == 3
    assert new_state.vacation.remaining == compute_remaining(5, 31, 3)
    assert len(new_state.history) == 1
    assert new_state.history[0].pdf_filename == pdf_filename(draft)


def test_settings_complete():
    incomplete = Settings(invoice_amount_eur=0, usdt_wallet="")
    assert settings_complete(incomplete) is False
    complete = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TAddr",
        from_party=PartyInfo(name="Ramin", email="a@b.com", location="X"),
        billed_to=PartyInfo(name="Boris", company="Co", location="Y"),
    )
    assert settings_complete(complete) is True


def test_pdf_filename():
    draft = InvoiceDraft(
        invoice_number=2334975,
        invoice_date=date(2026, 7, 31),
        amount_eur=5000,
        usdt_wallet="T",
        from_party=PartyInfo(name="Ramin"),
        billed_to=PartyInfo(name="Boris"),
        vacation_used=0,
        vacation_carried_over=0,
        vacation_remaining=31,
        month_label="July 2026",
    )
    assert pdf_filename(draft) == "Invoice-2334975-July-2026.pdf"
