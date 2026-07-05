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


def format_eur(value: float) -> str:
    """Format EUR amounts with thousands separators and two decimals."""
    return f"{value:,.2f}"


def render_invoice_pdf(draft: InvoiceDraft) -> bytes:
    """Render an invoice draft to PDF bytes."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["format_date"] = format_date
    env.filters["format_eur"] = format_eur
    template = env.get_template("invoice_pdf.html")
    html = template.render(draft=draft)
    buffer = BytesIO()
    HTML(string=html, base_url=str(PROJECT_ROOT)).write_pdf(buffer)
    return buffer.getvalue()
