"""Render invoice HTML templates to PDF via WeasyPrint."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.models import InvoiceDraft

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def format_date(value: date) -> str:
    """Format a date like '31 July, 2026' without platform-specific strftime flags."""
    return value.strftime("%d %B, %Y").lstrip("0").replace(" 0", " ", 1)


def format_date_short(value: date) -> str:
    """Format a date like '31 July' for compact lists within a known month."""
    return value.strftime("%d %B").lstrip("0").replace(" 0", " ", 1)


def format_eur(value: float) -> str:
    """Format EUR amounts with thousands separators and two decimals."""
    return f"{value:,.2f}"


def format_eur_invoice(value: float) -> str:
    """Format EUR amounts for invoice lines like '1500' or '1 500.50'."""
    if value == int(value):
        return str(int(value))
    return f"{value:,.2f}".replace(",", " ")


def render_invoice_html(draft: InvoiceDraft) -> str:
    """Render invoice HTML for preview or PDF generation."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["format_date"] = format_date
    env.filters["format_date_short"] = format_date_short
    env.filters["format_eur"] = format_eur
    env.filters["format_eur_invoice"] = format_eur_invoice
    template = env.get_template("invoice_pdf.html")
    return template.render(draft=draft)


def render_invoice_pdf(draft: InvoiceDraft) -> bytes:
    """Render an invoice draft to PDF bytes."""
    html = render_invoice_html(draft)
    buffer = BytesIO()
    HTML(string=html, base_url=str(PROJECT_ROOT)).write_pdf(buffer)
    return buffer.getvalue()
