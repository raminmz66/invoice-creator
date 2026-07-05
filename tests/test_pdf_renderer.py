"""Tests for PDF rendering."""

from datetime import date

from app.models import InvoiceDraft, PartyInfo
from app.pdf_renderer import format_date, format_eur, render_invoice_pdf


def test_format_date():
    assert format_date(date(2026, 7, 31)) == "31 July, 2026"
    assert format_date(date(2026, 7, 3)) == "3 July, 2026"


def test_format_eur():
    assert format_eur(5000) == "5,000.00"


def test_render_pdf_produces_bytes():
    draft = InvoiceDraft(
        invoice_number=2334975,
        invoice_date=date(2026, 7, 31),
        amount_eur=5000,
        usdt_wallet="TTestWallet",
        from_party=PartyInfo(name="Ramin", email="r@x.com", location="Mashad"),
        billed_to=PartyInfo(name="Boris", company="Initiative", location="France"),
        off_days=[date(2026, 7, 3)],
        vacation_used=7,
        vacation_carried_over=7,
        vacation_remaining=31,
        month_label="July 2026",
    )
    pdf = render_invoice_pdf(draft)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000
