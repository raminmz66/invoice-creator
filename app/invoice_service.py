"""Invoice generation business logic and vacation calculations."""

from __future__ import annotations

import calendar
from datetime import date

from app.models import (
    AppState,
    GenerateForm,
    InvoiceDraft,
    InvoiceHistoryEntry,
    Settings,
    VacationState,
)


def last_day_of_month(year: int, month: int) -> date:
    """Return the last calendar day for the given year and month."""
    return date(year, month, calendar.monthrange(year, month)[1])


def compute_remaining(carried_over: int, entitlement: int, used: int) -> int:
    """Calculate remaining vacation days from entitlement and usage."""
    return carried_over + entitlement - used


def settings_complete(settings: Settings) -> bool:
    """Return True when all required settings fields are filled."""
    return bool(
        settings.invoice_amount_eur > 0
        and settings.usdt_wallet.strip()
        and settings.from_party.name.strip()
        and settings.from_party.email.strip()
        and settings.from_party.location.strip()
        and settings.billed_to.name.strip()
        and settings.billed_to.company.strip()
        and settings.billed_to.location.strip()
    )


def build_draft(settings: Settings, state: AppState, form: GenerateForm) -> InvoiceDraft:
    """Build a resolved invoice draft from settings, state, and form input."""
    invoice_date = last_day_of_month(form.year, form.month)
    invoice_number = state.last_invoice_number + 1
    month_label = invoice_date.strftime("%B %Y")
    projected_used = state.vacation.used_this_year + len(form.off_days)
    projected_remaining = compute_remaining(
        state.vacation.carried_over,
        settings.annual_vacation_entitlement,
        projected_used,
    )
    return InvoiceDraft(
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        amount_eur=settings.invoice_amount_eur,
        usdt_wallet=settings.usdt_wallet,
        from_party=settings.from_party,
        billed_to=settings.billed_to,
        off_days=sorted(form.off_days),
        vacation_used=projected_used,
        vacation_carried_over=state.vacation.carried_over,
        vacation_remaining=projected_remaining,
        month_label=month_label,
    )


def validate_generate(
    settings: Settings | None,
    state: AppState | None,
    form: GenerateForm,
) -> list[str]:
    """Validate whether an invoice can be generated for the given input."""
    errors: list[str] = []
    if settings is None:
        errors.append("Settings not configured. Open Settings first.")
        return errors
    if not settings_complete(settings):
        errors.append("Settings incomplete. Fill all required fields.")
    if state is None:
        errors.append("State not initialized. Save settings to create initial state.")
        return errors
    if state.year != form.year:
        errors.append("New year detected. Apply vacation reset before generating.")
        return errors
    remaining_before = state.vacation.remaining
    if len(form.off_days) > remaining_before:
        errors.append(f"You have {remaining_before} day(s) remaining but added {len(form.off_days)} off day(s).")
    return errors


def apply_year_rollover(
    state: AppState,
    settings: Settings,
    target_year: int,
    carried_over: int,
) -> AppState:
    """Reset vacation tracking when generating in a new calendar year."""
    used = 0
    return AppState(
        last_invoice_number=state.last_invoice_number,
        vacation=VacationState(
            used_this_year=used,
            carried_over=carried_over,
            remaining=compute_remaining(carried_over, settings.annual_vacation_entitlement, used),
        ),
        year=target_year,
        history=state.history,
    )


def pdf_filename(draft: InvoiceDraft) -> str:
    """Build the download filename for a generated invoice PDF."""
    month_slug = draft.invoice_date.strftime("%B-%Y")
    return f"Invoice-{draft.invoice_number}-{month_slug}.pdf"


def apply_generation(state: AppState, draft: InvoiceDraft, form: GenerateForm) -> AppState:
    """Return updated state after a successful invoice generation."""
    new_vacation = VacationState(
        used_this_year=draft.vacation_used,
        carried_over=state.vacation.carried_over,
        remaining=draft.vacation_remaining,
    )
    entry = InvoiceHistoryEntry(
        invoice_number=draft.invoice_number,
        date=draft.invoice_date,
        off_days=form.off_days,
        pdf_filename=pdf_filename(draft),
    )
    return AppState(
        last_invoice_number=draft.invoice_number,
        vacation=new_vacation,
        year=form.year,
        history=[*state.history, entry],
    )


def default_state_from_settings(settings: Settings, seed_invoice_number: int) -> AppState:
    """Create initial application state when settings are first saved."""
    used = 0
    return AppState(
        last_invoice_number=seed_invoice_number,
        vacation=VacationState(
            used_this_year=used,
            carried_over=0,
            remaining=compute_remaining(0, settings.annual_vacation_entitlement, used),
        ),
        year=date.today().year,
    )
