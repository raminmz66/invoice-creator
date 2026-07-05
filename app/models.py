"""Pydantic domain models for invoice settings, state, and generation."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class PartyInfo(BaseModel):
    """Contact details for the invoice sender or recipient."""

    name: str = ""
    email: str = ""
    company: str = ""
    location: str = ""


class Settings(BaseModel):
    """Persistent invoice configuration edited on the Settings page."""

    model_config = ConfigDict(populate_by_name=True)

    invoice_amount_eur: float = Field(ge=0, description="Fixed monthly invoice amount in EUR")
    usdt_wallet: str = Field(default="", description="USDT TRC20 wallet address for payment")
    from_party: PartyInfo = Field(default_factory=PartyInfo, alias="from")
    billed_to: PartyInfo = Field(default_factory=PartyInfo)
    annual_vacation_entitlement: int = Field(ge=0, default=31)


class VacationState(BaseModel):
    """Tracked vacation and off-day balances."""

    used_this_year: int = Field(ge=0, default=0)
    carried_over: int = Field(ge=0, default=0)
    remaining: int = Field(ge=0, default=0)


class InvoiceHistoryEntry(BaseModel):
    """Record of a previously generated invoice."""

    invoice_number: int = Field(ge=1)
    date: date
    off_days: list[date] = Field(default_factory=list)
    pdf_filename: str


class AppState(BaseModel):
    """Runtime state persisted between monthly invoice generations."""

    last_invoice_number: int = Field(ge=0, default=0)
    vacation: VacationState = Field(default_factory=VacationState)
    year: int = Field(ge=2000, le=2100)
    history: list[InvoiceHistoryEntry] = Field(default_factory=list)


class InvoiceDraft(BaseModel):
    """Fully resolved invoice data used for PDF rendering."""

    invoice_number: int = Field(ge=1)
    invoice_date: date
    amount_eur: float = Field(ge=0)
    usdt_wallet: str
    from_party: PartyInfo
    billed_to: PartyInfo
    off_days: list[date] = Field(default_factory=list)
    vacation_used: int = Field(ge=0)
    vacation_carried_over: int = Field(ge=0)
    vacation_remaining: int = Field(ge=0)
    month_label: str


class GenerateForm(BaseModel):
    """User input for a monthly invoice generation request."""

    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    off_days: list[date] = Field(default_factory=list)
