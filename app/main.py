"""FastAPI application for invoice generation."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.invoice_service import (
    apply_generation,
    apply_year_rollover,
    build_draft,
    compute_remaining,
    pdf_filename,
    settings_complete,
    validate_generate,
)
from app.models import AppState, GenerateForm, PartyInfo, Settings, VacationState
from app.pdf_renderer import format_date, format_date_short, format_eur, format_eur_invoice, render_invoice_pdf
from app.storage import load_settings, load_state, save_settings, save_state

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Invoice Creator")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
templates.env.filters["format_date"] = format_date
templates.env.filters["format_date_short"] = format_date_short
templates.env.filters["format_eur"] = format_eur
templates.env.filters["format_eur_invoice"] = format_eur_invoice


def _parse_month_value(month_value: str) -> tuple[int, int]:
    year_str, month_str = month_value.split("-", maxsplit=1)
    return int(year_str), int(month_str)


def _today_month_value() -> str:
    today = date.today()
    return f"{today.year}-{today.month:02d}"


def _parse_off_days(raw_values: list[str]) -> list[date]:
    return [date.fromisoformat(value) for value in raw_values if value]


def _build_context(request: Request, **extra: object) -> dict[str, object]:
    return {"request": request, **extra}


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/generate", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings_get(request: Request) -> HTMLResponse:
    settings = load_settings()
    state = load_state()
    remaining = None
    if state and settings:
        remaining = state.vacation.remaining
    elif settings:
        remaining = compute_remaining(0, settings.annual_vacation_entitlement, 0)

    return templates.TemplateResponse(
        request,
        "settings.html",
        _build_context(
            request,
            settings=settings,
            state=state,
            remaining=remaining,
            saved=request.query_params.get("saved") == "1",
            errors=[],
        ),
    )


@app.post("/settings", response_class=HTMLResponse)
async def settings_post(request: Request) -> HTMLResponse:
    form = await request.form()
    errors: list[str] = []

    try:
        invoice_amount_eur = float(form.get("invoice_amount_eur", 0))
    except ValueError:
        invoice_amount_eur = -1
        errors.append("Monthly amount must be a number.")

    settings = Settings(
        invoice_amount_eur=invoice_amount_eur,
        usdt_wallet=str(form.get("usdt_wallet", "")).strip(),
        from_party=PartyInfo(
            name=str(form.get("from_name", "")).strip(),
            email=str(form.get("from_email", "")).strip(),
            location=str(form.get("from_location", "")).strip(),
        ),
        billed_to=PartyInfo(
            name=str(form.get("billed_to_name", "")).strip(),
            company=str(form.get("billed_to_company", "")).strip(),
            location=str(form.get("billed_to_location", "")).strip(),
        ),
        annual_vacation_entitlement=int(form.get("annual_vacation_entitlement", 31)),
    )

    if not settings_complete(settings):
        errors.append("Fill all required settings fields.")

    used_this_year = int(form.get("used_this_year", 0))
    carried_over = int(form.get("carried_over", 0))
    last_invoice_number = int(form.get("last_invoice_number", 0))
    remaining = compute_remaining(
        carried_over,
        settings.annual_vacation_entitlement,
        used_this_year,
    )

    if errors:
        return templates.TemplateResponse(
            request,
            "settings.html",
            _build_context(
                request,
                settings=settings,
                state=AppState(
                    last_invoice_number=last_invoice_number,
                    vacation=VacationState(
                        used_this_year=used_this_year,
                        carried_over=carried_over,
                        remaining=remaining,
                    ),
                    year=date.today().year,
                ),
                remaining=remaining,
                saved=False,
                errors=errors,
            ),
            status_code=400,
        )

    save_settings(settings)
    existing_state = load_state()
    save_state(
        AppState(
            last_invoice_number=last_invoice_number,
            vacation=VacationState(
                used_this_year=used_this_year,
                carried_over=carried_over,
                remaining=remaining,
            ),
            year=date.today().year,
            history=existing_state.history if existing_state else [],
        )
    )
    return RedirectResponse(url="/settings?saved=1", status_code=303)


@app.get("/generate", response_class=HTMLResponse)
def generate_get(request: Request, month: str | None = None) -> HTMLResponse:
    settings = load_settings()
    state = load_state()
    month_value = month or _today_month_value()
    year, month_num = _parse_month_value(month_value)

    if not settings or not state or not settings_complete(settings):
        return templates.TemplateResponse(
            request,
            "generate.html",
            _build_context(
                request,
                settings_ready=False,
                month_value=month_value,
                errors=[],
            ),
        )

    generate_form = GenerateForm(year=year, month=month_num, off_days=[])
    draft = build_draft(settings, state, generate_form)
    show_year_rollover = state.year != year
    rollover_carried_over = state.vacation.remaining if show_year_rollover else state.vacation.carried_over

    return templates.TemplateResponse(
        request,
        "generate.html",
        _build_context(
            request,
            settings_ready=True,
            settings=settings,
            state=state,
            month_value=month_value,
            draft=draft,
            off_days=[],
            errors=[],
            show_year_rollover=show_year_rollover,
            rollover_carried_over=rollover_carried_over,
            base_used=state.vacation.used_this_year,
            base_remaining=state.vacation.remaining,
            entitlement=settings.annual_vacation_entitlement,
            carried_over=state.vacation.carried_over,
        ),
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate_post(request: Request) -> Response:
    form = await request.form()
    settings = load_settings()
    state = load_state()
    month_value = str(form.get("month", _today_month_value()))
    year, month_num = _parse_month_value(month_value)
    off_days = _parse_off_days([str(value) for value in form.getlist("off_days")])
    action = str(form.get("action", "download"))
    generate_form = GenerateForm(year=year, month=month_num, off_days=off_days)
    show_year_rollover = bool(state and state.year != year)
    rollover_carried_over = int(
        form.get("rollover_carried_over", state.vacation.remaining if state and show_year_rollover else 0)
    )

    if action == "apply_rollover":
        if not settings or not state or not settings_complete(settings):
            return templates.TemplateResponse(
                request,
                "generate.html",
                _build_context(
                    request,
                    settings_ready=False,
                    month_value=month_value,
                    errors=["Settings not configured. Open Settings first."],
                ),
                status_code=400,
            )
        if not form.get("rollover_reset"):
            draft = build_draft(settings, state, generate_form)
            return templates.TemplateResponse(
                request,
                "generate.html",
                _build_context(
                    request,
                    settings_ready=True,
                    settings=settings,
                    state=state,
                    month_value=month_value,
                    draft=draft,
                    off_days=off_days,
                    errors=["Confirm reset used days to 0 before applying."],
                    show_year_rollover=True,
                    rollover_carried_over=rollover_carried_over,
                    base_used=state.vacation.used_this_year,
                    base_remaining=state.vacation.remaining,
                    entitlement=settings.annual_vacation_entitlement,
                    carried_over=state.vacation.carried_over,
                ),
                status_code=400,
            )
        save_state(apply_year_rollover(state, settings, year, rollover_carried_over))
        return RedirectResponse(url=f"/generate?month={month_value}", status_code=303)

    errors = validate_generate(settings, state, generate_form)
    draft = build_draft(settings, state, generate_form) if settings and state else None

    if errors:
        return templates.TemplateResponse(
            request,
            "generate.html",
            _build_context(
                request,
                settings_ready=bool(settings and state and settings_complete(settings)),
                settings=settings,
                state=state,
                month_value=month_value,
                draft=draft,
                off_days=off_days,
                errors=errors,
                show_year_rollover=show_year_rollover,
                rollover_carried_over=rollover_carried_over,
                base_used=state.vacation.used_this_year if state else 0,
                base_remaining=state.vacation.remaining if state else 0,
                entitlement=settings.annual_vacation_entitlement if settings else 31,
                carried_over=state.vacation.carried_over if state else 0,
            ),
            status_code=400,
        )

    assert settings is not None and state is not None and draft is not None

    try:
        pdf_bytes = render_invoice_pdf(draft)
    except Exception:
        logger.exception("PDF generation failed for invoice %s", draft.invoice_number)
        return templates.TemplateResponse(
            request,
            "generate.html",
            _build_context(
                request,
                settings_ready=True,
                settings=settings,
                state=state,
                month_value=month_value,
                draft=draft,
                off_days=off_days,
                errors=["PDF generation failed. Please try again."],
                show_year_rollover=show_year_rollover,
                rollover_carried_over=rollover_carried_over,
                base_used=state.vacation.used_this_year,
                base_remaining=state.vacation.remaining,
                entitlement=settings.annual_vacation_entitlement,
                carried_over=state.vacation.carried_over,
            ),
            status_code=500,
        )

    filename = pdf_filename(draft)
    disposition = "inline" if action == "preview" else "attachment"

    if action == "download":
        save_state(apply_generation(state, draft, generate_form))

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


@app.get("/generate/preview", response_class=Response)
def generate_preview(
    month: str,
    off_days: list[str] | None = None,
) -> Response:
    settings = load_settings()
    state = load_state()
    if not settings or not state:
        return Response(status_code=400)

    year, month_num = _parse_month_value(month)
    generate_form = GenerateForm(
        year=year,
        month=month_num,
        off_days=_parse_off_days(off_days or []),
    )
    errors = validate_generate(settings, state, generate_form)
    if errors:
        return Response(content=errors[0], status_code=400)

    draft = build_draft(settings, state, generate_form)
    pdf_bytes = render_invoice_pdf(draft)
    filename = pdf_filename(draft)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
