from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PartyInfo(BaseModel):
    name: str = ""
    email: str = ""
    company: str = ""
    location: str = ""


class Settings(BaseModel):
    invoice_amount_eur: float = Field(ge=0)
    usdt_wallet: str = ""
    from_party: PartyInfo = Field(default_factory=PartyInfo, alias="from")
    billed_to: PartyInfo = Field(default_factory=PartyInfo)
    annual_vacation_entitlement: int = Field(ge=0, default=31)

    model_config = {"populate_by_name": True}


class VacationState(BaseModel):
    used_this_year: int = Field(ge=0, default=0)
    carried_over: int = Field(ge=0, default=0)
    remaining: int = Field(ge=0, default=0)


class InvoiceHistoryEntry(BaseModel):
    invoice_number: int
    date: date
    off_days: list[date] = Field(default_factory=list)
    pdf_filename: str


class AppState(BaseModel):
    last_invoice_number: int = Field(ge=0, default=0)
    vacation: VacationState = Field(default_factory=VacationState)
    year: int
    history: list[InvoiceHistoryEntry] = Field(default_factory=list)


class InvoiceDraft(BaseModel):
    invoice_number: int
    invoice_date: date
    amount_eur: float
    usdt_wallet: str
    from_party: PartyInfo
    billed_to: PartyInfo
    off_days: list[date] = Field(default_factory=list)
    vacation_used: int
    vacation_carried_over: int
    vacation_remaining: int
    month_label: str


class GenerateForm(BaseModel):
    year: int
    month: int
    off_days: list[date] = Field(default_factory=list)
