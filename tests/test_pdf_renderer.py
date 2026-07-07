"""Tests for PDF rendering."""

from datetime import date
from pathlib import Path

import pytest

from app.models import InvoiceDraft, PartyInfo
from app.pdf_renderer import format_date, format_eur, format_eur_invoice, render_invoice_html, render_invoice_pdf


@pytest.fixture
def sample_draft():
    return InvoiceDraft(
        invoice_number=2334974,
        invoice_date=date(2026, 6, 30),
        amount_eur=1500,
        usdt_wallet="TCEvAY15PUDMrb5uu35F1EhG21u2RYHtoS",
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
        off_days=[],
        vacation_used=6,
        vacation_carried_over=7,
        vacation_remaining=31,
        month_label="June 2026",
    )


def test_format_date():
    assert format_date(date(2026, 7, 31)) == "31 July, 2026"
    assert format_date(date(2026, 7, 3)) == "3 July, 2026"


def test_format_eur():
    assert format_eur(5000) == "5,000.00"


def test_format_eur_invoice():
    assert format_eur_invoice(1500) == "1500"
    assert format_eur_invoice(5000) == "5000"
    assert format_eur_invoice(1500.5) == "1 500.50"


def test_invoice_document_css_uses_reference_tokens():
    css = (Path(__file__).resolve().parent.parent / "static" / "invoice-document.css").read_text(encoding="utf-8")
    lowered = css.lower()
    assert "googleapis" not in lowered
    assert "cormorant" not in lowered
    assert "#96ee71" in lowered
    assert "#e9c119" in lowered
    assert "oswald" in lowered
    assert "nunito" in lowered
    assert "@font-face" in lowered


def test_pdf_html_uses_reference_assets(sample_draft):
    html = render_invoice_html(sample_draft)
    assert "static/invoice/footer-green.png" in html
    assert "static/invoice/footer-navy.png" in html
    assert "static/invoice/image3.png" in html
    assert "static/invoice/signature.png" not in html
    assert "invoice-signature.svg" not in html
    assert "footer-waves" not in html
    assert "off-day-chip" not in html
    assert "chrome-input" not in html
    assert "Payment for June 2026" in html
    assert "€ 1500" in html


def test_pdf_html_has_four_column_items_table(sample_draft):
    html = render_invoice_html(sample_draft)
    assert 'class="items"' in html
    assert "items-total" in html
    assert html.count("<td") >= 8


def test_render_pdf_produces_bytes(sample_draft):
    pdf = render_invoice_pdf(sample_draft)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 5000


def test_pdf_is_single_letter_page(sample_draft):
    from weasyprint import HTML

    from app.pdf_renderer import PROJECT_ROOT, render_invoice_html

    doc = HTML(
        string=render_invoice_html(sample_draft),
        base_url=str(PROJECT_ROOT),
    ).render()
    assert len(doc.pages) == 1
    # US Letter = 8.5in x 11in = 816px x 1056px at 96 CSS dpi
    assert round(doc.pages[0].width) == 816
    assert round(doc.pages[0].height) == 1056
