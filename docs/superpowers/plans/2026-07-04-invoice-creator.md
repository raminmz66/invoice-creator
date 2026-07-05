# Invoice Creator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local FastAPI web app that generates monthly PDF invoices (EUR amount, USDT wallet), auto-tracks invoice numbers and vacation balances, and launches from the Ubuntu applications menu.

**Architecture:** FastAPI serves HTML forms for Settings and Generate pages. JSON files persist settings and state. Invoice service computes dates, numbers, and vacation math. Jinja2 HTML template renders to PDF via WeasyPrint. A shell launch script starts the server and opens the browser; a `.desktop` file registers the app in Ubuntu.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Jinja2, WeasyPrint, Pydantic, pytest, uv (package manager)

**Specs (read as needed, not cover-to-cover):**

| Doc | Path | Use for |
|-----|------|---------|
| Functional | `docs/superpowers/specs/2026-07-04-invoice-creator-design.md` | Business logic, data model, validation, launcher, errors |
| UI/UX | `docs/superpowers/specs/2026-07-04-invoice-creator-ui-design.md` | Design tokens, page layouts, interactions, PDF parity, copy |

**This plan** defines task order and file paths. When specs and plan disagree: functional spec wins for behavior; UI spec wins for appearance.

**UI implementation skills:** Apply `.agents/skills/frontend-design/SKILL.md` during Tasks 5–6, constrained by the UI spec (paper invoice aesthetic — do not override tokens/layout without updating the UI spec).

---

## File Structure

```
invoice-creator/
├── pyproject.toml
├── README.md
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI routes
│   ├── models.py               # Pydantic models
│   ├── storage.py              # JSON load/save
│   ├── invoice_service.py      # Business logic
│   ├── pdf_renderer.py         # HTML → PDF
│   └── templates/
│       ├── base.html           # Layout shell
│       ├── settings.html       # Settings form
│       ├── generate.html       # Generate form
│       └── invoice_pdf.html    # PDF-only template
├── static/
│   ├── invoice-document.css    # Shared invoice paper styles (web + PDF)
│   └── styles.css              # App chrome (desk, top bar, forms, buttons)
├── data/
│   ├── .gitkeep
│   ├── settings.example.json   # Committed example
│   └── state.example.json      # Committed example
├── tests/
│   ├── __init__.py
│   ├── test_invoice_service.py
│   └── test_storage.py
├── scripts/
│   ├── launch.sh
│   └── install-desktop.sh
├── assets/
│   └── icon.png
└── invoice-creator.desktop.in  # Template for desktop entry
```

Runtime data (`data/settings.json`, `data/state.json`) is gitignored; created on first Settings save or seeded from examples.

---

### Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `app/__init__.py`
- Create: `data/.gitkeep`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "invoice-creator"
version = "0.1.0"
description = "Local monthly invoice PDF generator"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "jinja2>=3.1.0",
    "weasyprint>=63.0",
    "pydantic>=2.0",
    "python-multipart>=0.0.12",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "httpx>=0.27.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.py[cod]
.venv/
data/settings.json
data/state.json
*.pdf
.server.pid
```

- [ ] **Step 3: Install dependencies**

Run: `cd /home/ramin/invoice-creator && uv sync --extra dev`
Expected: Virtual env created, packages installed

- [ ] **Step 4: Verify pytest runs**

Run: `uv run pytest --co -q`
Expected: `no tests ran` (empty suite, exit 0)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore app/__init__.py tests/__init__.py data/.gitkeep
git commit -m "chore: scaffold invoice-creator project"
```

---

### Task 2: Data models

**Files:**
- Create: `app/models.py`
- Create: `data/settings.example.json`
- Create: `data/state.example.json`

- [ ] **Step 1: Write `app/models.py`**

```python
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
```

- [ ] **Step 2: Create example JSON files**

`data/settings.example.json`:
```json
{
  "invoice_amount_eur": 5000,
  "usdt_wallet": "",
  "from": {
    "name": "Ramin Maazallahi",
    "email": "r.mazallahi-ext@initiative-crm.com",
    "company": "",
    "location": "Mashad, Iran"
  },
  "billed_to": {
    "name": "Boris Clement",
    "company": "Initiative solutions",
    "email": "",
    "location": "Valreas, France"
  },
  "annual_vacation_entitlement": 31
}
```

`data/state.example.json`:
```json
{
  "last_invoice_number": 2334974,
  "vacation": {
    "used_this_year": 6,
    "carried_over": 7,
    "remaining": 31
  },
  "year": 2026,
  "history": []
}
```

- [ ] **Step 3: Commit**

```bash
git add app/models.py data/settings.example.json data/state.example.json
git commit -m "feat: add Pydantic models and example data files"
```

---

### Task 3: Storage layer

**Files:**
- Create: `app/storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write failing storage test**

```python
# tests/test_storage.py
import json
from pathlib import Path

import pytest

from app.models import Settings, AppState, VacationState
from app.storage import load_settings, save_settings, load_state, save_state, DATA_DIR


@pytest.fixture
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setattr("app.storage.DATA_DIR", tmp_path)
    return tmp_path


def test_save_and_load_settings(isolated_data):
    settings = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TTest123",
        **{"from": {"name": "Ramin", "location": "Mashad"}},
        billed_to={"name": "Boris", "company": "Initiative"},
    )
    save_settings(settings)
    loaded = load_settings()
    assert loaded.invoice_amount_eur == 5000
    assert loaded.usdt_wallet == "TTest123"


def test_load_settings_missing_returns_none(isolated_data):
    assert load_settings() is None


def test_save_and_load_state(isolated_data):
    state = AppState(
        last_invoice_number=100,
        vacation=VacationState(used_this_year=2, carried_over=5, remaining=34),
        year=2026,
    )
    save_state(state)
    loaded = load_state()
    assert loaded.last_invoice_number == 100
    assert loaded.vacation.remaining == 34
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_storage.py -v`
Expected: FAIL — `ModuleNotFoundError: app.storage`

- [ ] **Step 3: Implement `app/storage.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

from app.models import Settings, AppState

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SETTINGS_PATH = DATA_DIR / "settings.json"
STATE_PATH = DATA_DIR / "state.json"


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def load_settings() -> Settings | None:
    raw = _read_json(SETTINGS_PATH)
    return Settings.model_validate(raw) if raw else None


def save_settings(settings: Settings) -> None:
    _write_json(SETTINGS_PATH, settings.model_dump(by_alias=True))


def load_state() -> AppState | None:
    raw = _read_json(STATE_PATH)
    return AppState.model_validate(raw) if raw else None


def save_state(state: AppState) -> None:
    _write_json(STATE_PATH, state.model_dump(mode="json"))
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_storage.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/storage.py tests/test_storage.py
git commit -m "feat: add JSON storage layer for settings and state"
```

---

### Task 4: Invoice service (business logic)

**Files:**
- Create: `app/invoice_service.py`
- Create: `tests/test_invoice_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_invoice_service.py
from datetime import date

import pytest

from app.models import Settings, AppState, VacationState, PartyInfo, GenerateForm
from app.invoice_service import (
    last_day_of_month,
    compute_remaining,
    build_draft,
    apply_generation,
    validate_generate,
    settings_complete,
)


def test_last_day_of_month():
    assert last_day_of_month(2026, 6) == date(2026, 6, 30)
    assert last_day_of_month(2026, 2) == date(2026, 2, 28)


def test_compute_remaining():
    assert compute_remaining(carried_over=7, entitlement=31, used=6) == 32


def test_build_draft_increments_invoice_number():
    settings = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TWallet",
        **{"from": PartyInfo(name="Ramin")},
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
        **{"from": PartyInfo(name="Ramin")},
        billed_to=PartyInfo(name="Boris"),
    )
    state = AppState(
        last_invoice_number=1,
        vacation=VacationState(used_this_year=0, carried_over=0, remaining=1),
        year=2026,
    )
    form = GenerateForm(
        year=2026, month=7,
        off_days=[date(2026, 7, 1), date(2026, 7, 2)],
    )
    errors = validate_generate(settings, state, form)
    assert any("remaining" in e.lower() for e in errors)


def test_apply_generation_updates_state():
    settings = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TWallet",
        **{"from": PartyInfo(name="Ramin")},
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


def test_settings_complete():
    incomplete = Settings(invoice_amount_eur=0, usdt_wallet="")
    assert settings_complete(incomplete) is False
    complete = Settings(
        invoice_amount_eur=5000,
        usdt_wallet="TAddr",
        **{"from": PartyInfo(name="Ramin", email="a@b.com", location="X")},
        billed_to=PartyInfo(name="Boris", company="Co", location="Y"),
    )
    assert settings_complete(complete) is True
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `uv run pytest tests/test_invoice_service.py -v`

- [ ] **Step 3: Implement `app/invoice_service.py`**

```python
from __future__ import annotations

import calendar
from datetime import date

from app.models import (
    Settings,
    AppState,
    InvoiceDraft,
    GenerateForm,
    InvoiceHistoryEntry,
    VacationState,
)


def last_day_of_month(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def compute_remaining(carried_over: int, entitlement: int, used: int) -> int:
    return carried_over + entitlement - used


def settings_complete(settings: Settings) -> bool:
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
    errors: list[str] = []
    if settings is None:
        errors.append("Settings not configured. Open Settings first.")
        return errors
    if not settings_complete(settings):
        errors.append("Settings incomplete. Fill all required fields.")
    if state is None:
        errors.append("State not initialized. Save settings to create initial state.")
        return errors
    remaining_before = state.vacation.remaining
    if len(form.off_days) > remaining_before:
        errors.append(
            f"You have {remaining_before} day(s) remaining but added {len(form.off_days)} off day(s)."
        )
    return errors


def pdf_filename(draft: InvoiceDraft) -> str:
    month_slug = draft.invoice_date.strftime("%B-%Y")
    return f"Invoice-{draft.invoice_number}-{month_slug}.pdf"


def apply_generation(
    state: AppState, draft: InvoiceDraft, form: GenerateForm
) -> AppState:
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
    used = 0
    carried = settings.annual_vacation_entitlement  # user overrides via settings form
    return AppState(
        last_invoice_number=seed_invoice_number,
        vacation=VacationState(
            used_this_year=used,
            carried_over=0,
            remaining=compute_remaining(0, settings.annual_vacation_entitlement, used),
        ),
        year=date.today().year,
    )
```

Note: `default_state_from_settings` is a fallback; the Settings form will also accept explicit `carried_over`, `used_this_year`, and `seed_invoice_number` fields (wired in Task 6).

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_invoice_service.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add app/invoice_service.py tests/test_invoice_service.py
git commit -m "feat: add invoice business logic and vacation math"
```

---

### Task 5: PDF renderer

**UI spec:** `2026-07-04-invoice-creator-ui-design.md` → Design tokens, PDF parity, Generate page paper card content

**Files:**
- Create: `app/pdf_renderer.py`
- Create: `app/templates/invoice_pdf.html`
- Create: `static/invoice-document.css`

- [ ] **Step 1: Create shared invoice CSS**

Create `static/invoice-document.css` using tokens from the UI spec:

- `--paper: #F7F4EE`, `--ink: #2C2C2C`, `--rule: #D4CFC6`, etc.
- Fonts: Cormorant Garamond (title, amount) + Source Sans 3 (body)
- A4 padding 2.5cm, hairline table borders, two-column parties layout

Both `invoice_pdf.html` and the Generate page paper card must `@import` or link this file (see UI spec → **PDF parity**).

- [ ] **Step 2: Create PDF HTML template**

`app/templates/invoice_pdf.html` — structure per UI spec **Generate page → Paper card content** and functional spec **PDF Layout**:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="..."> <!-- invoice-document.css; inline for WeasyPrint if needed -->
  <style>
    @page { size: A4; margin: 0; }
    /* Prefer importing shared token values from invoice-document.css */
    body { font-family: 'Source Sans 3', sans-serif; font-size: 11pt; color: #2C2C2C; background: #F7F4EE; }
    h1 { font-family: 'Cormorant Garamond', serif; font-size: 28px; font-weight: 500; }
    .invoice-no { font-size: 10pt; margin-bottom: 0.5em; }
    h1 { font-size: 18pt; font-weight: normal; margin: 0 0 1em 0; }
    .date { margin-bottom: 1.5em; }
    .parties { display: table; width: 100%; margin-bottom: 2em; }
    .party { display: table-cell; width: 50%; vertical-align: top; }
    .party-label { font-weight: bold; margin-bottom: 0.5em; }
    .party-line { margin: 0.2em 0; }
    table.items { width: 100%; border-collapse: collapse; margin: 1.5em 0; }
    table.items th, table.items td { border: 1px solid #ccc; padding: 8px; text-align: left; }
    table.items td.amount { text-align: right; }
    .wallet { margin: 1.5em 0; }
    .section-title { font-weight: bold; margin-top: 1.5em; margin-bottom: 0.5em; }
    .off-day { margin-left: 1em; }
    .vacation-line { margin: 0.3em 0; }
  </style>
</head>
<body>
  <div class="invoice-no">No. {{ draft.invoice_number }}</div>
  <h1>Invoice</h1>
  <div class="date">Date: {{ draft.invoice_date.strftime('%-d %B, %Y') if draft.invoice_date.day else draft.invoice_date.strftime('%d %B, %Y') }}</div>

  <div class="parties">
    <div class="party">
      <div class="party-label">Billed to:</div>
      <div class="party-line">{{ draft.billed_to.name }}</div>
      <div class="party-line">{{ draft.billed_to.company }}</div>
      <div class="party-line">{{ draft.billed_to.location }}</div>
    </div>
    <div class="party">
      <div class="party-label">From:</div>
      <div class="party-line">{{ draft.from_party.name }}</div>
      <div class="party-line">{{ draft.from_party.email }}</div>
      <div class="party-line">{{ draft.from_party.location }}</div>
    </div>
  </div>

  <table class="items">
    <thead>
      <tr><th>Description</th><th>Amount</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Professional services — {{ draft.month_label }}</td>
        <td class="amount">€{{ '{:,.2f}'.format(draft.amount_eur) }}</td>
      </tr>
    </tbody>
  </table>

  <div class="wallet">
    <strong>Wallet ID (USDT TRC20):</strong><br>
    {{ draft.usdt_wallet }}
  </div>

  {% if draft.off_days %}
  <div class="section-title">Off days this month:</div>
  {% for d in draft.off_days %}
  <div class="off-day">{{ d.strftime('%-d %B, %Y') if d.day else d.strftime('%d %B, %Y') }}</div>
  {% endfor %}
  {% endif %}

  <div class="section-title">Vacations (and Off days):</div>
  <div class="vacation-line">Total used this year: {{ draft.vacation_used }} days</div>
  <div class="vacation-line">Carried over last year(s): {{ draft.vacation_carried_over }} days</div>
  <div class="vacation-line">Remaining: {{ draft.vacation_remaining }} days</div>
</body>
</html>
```

Use `%-d` only on Linux; in implementation, add a Jinja filter `format_date` to avoid platform issues:

```python
def format_date(d: date) -> str:
    return d.strftime("%d %B, %Y").lstrip("0").replace(" 0", " ", 1)
```

- [ ] **Step 3: Implement `app/pdf_renderer.py`**

```python
from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.models import InvoiceDraft

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def format_date(d: date) -> str:
    return d.strftime("%d %B, %Y").lstrip("0").replace(" 0", " ", 1)


def render_invoice_pdf(draft: InvoiceDraft) -> bytes:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["format_date"] = format_date
    template = env.get_template("invoice_pdf.html")
    html = template.render(draft=draft)
    buffer = BytesIO()
    HTML(string=html).write_pdf(buffer)
    return buffer.getvalue()
```

Update template to use `{{ d | format_date }}` instead of strftime.

- [ ] **Step 4: Manual smoke test**

Create a small script or pytest:

```python
def test_render_pdf_produces_bytes():
    from app.models import InvoiceDraft, PartyInfo
    from app.pdf_renderer import render_invoice_pdf
    from datetime import date

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
```

Run: `uv run pytest tests/test_pdf_renderer.py -v` (create file with above test)

- [ ] **Step 5: Commit**

```bash
git add app/pdf_renderer.py app/templates/invoice_pdf.html static/invoice-document.css tests/test_pdf_renderer.py
git commit -m "feat: add WeasyPrint PDF renderer and invoice template"
```

---

### Task 6: FastAPI app and routes

**UI spec:** `2026-07-04-invoice-creator-ui-design.md` → Global chrome, Generate page, Settings page, components, copy guidelines

**Functional spec:** `2026-07-04-invoice-creator-design.md` → Data flow on Generate, error handling, Settings fields

**Files:**
- Create: `app/main.py`
- Create: `app/templates/base.html`
- Create: `app/templates/settings.html`
- Create: `app/templates/generate.html`
- Create: `static/styles.css` (app chrome only — desk, top bar, buttons; invoice content uses `invoice-document.css`)

- [ ] **Step 1: Implement `app/main.py`**

Key routes:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Redirect to `/generate` |
| GET/POST | `/settings` | Edit and save settings + initial state |
| GET/POST | `/generate` | Show form, validate, generate PDF |
| GET | `/generate/preview` | HTML preview of invoice (same draft data) |

POST `/generate` flow:
1. Parse form: `year`, `month`, `off_days` (multiple date inputs)
2. Load settings + state
3. `validate_generate()` — if errors, re-render form with messages
4. `build_draft()` → `render_invoice_pdf()` — on exception, show error, do NOT save state
5. `apply_generation()` → `save_state()`
6. Return `Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})`

Settings POST saves settings and initializes/updates state fields:
- `seed_invoice_number`, `used_this_year`, `carried_over` (recalculate remaining)

- [ ] **Step 2: Create base template and pages**

Implement layouts exactly as wireframed in the UI spec:

**`app/templates/base.html`**
- Top bar: "Invoice Creator" left, contextual nav right (`Settings →` / `← Generate`)
- Desk background (`--desk`), block content area

**`app/templates/generate.html`** (UI spec → Generate page)
- Month selector above paper: `Invoice for: [month ▾]`
- A4 paper card reusing `invoice-document.css` + editable off-day chips
- Live vacation summary (client-side JS)
- Buttons below paper: Preview PDF (outline) | Generate & Download (filled)
- First-run state: "Set up your invoice details first" with link to Settings

**`app/templates/settings.html`** (UI spec → Settings page)
- Narrower paper card (640px), sections: Payment / From / Billed to / Vacation & tracking
- Computed remaining (read-only), Save settings button, success toast

Read `.agents/skills/frontend-design/SKILL.md` for polish within the UI spec tokens — do not swap to generic SaaS aesthetics.

- [ ] **Step 3: Wire static files**

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
```

- [ ] **Step 4: Manual smoke test**

Run: `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`
1. Open `/settings` — save settings; confirm toast and layout match UI spec
2. Open `/generate` — verify paper card matches UI spec; add off day; confirm live vacation update
3. Preview PDF and Generate — verify web paper and PDF look identical (UI spec success criterion #1)
4. Verify `data/state.json` updated only after successful Generate

- [ ] **Step 5: Commit**

```bash
git add app/main.py app/templates/ static/
git commit -m "feat: add FastAPI web UI for settings and invoice generation"
```

---

### Task 7: Year rollover handling

**UI spec:** `2026-07-04-invoice-creator-ui-design.md` → Year rollover banner  
**Functional spec:** `2026-07-04-invoice-creator-design.md` → Vacation math → Year rollover

**Files:**
- Modify: `app/main.py`
- Modify: `app/templates/generate.html`

- [ ] **Step 1: Detect year mismatch on GET `/generate`**

If `state.year != selected year`, show banner per UI spec (above paper card):

> **New year detected.** Confirm vacation reset before generating.  
> ☐ Reset used days to 0 · Carried over: [input] days · [Apply]

POST handler applies reset before validation when confirmed.

- [ ] **Step 2: Test manually**

Set `state.year` to 2025 in JSON, open generate for 2026, confirm banner appears.

- [ ] **Step 3: Commit**

```bash
git add app/main.py app/templates/generate.html
git commit -m "feat: add year rollover prompt for vacation reset"
```

---

### Task 8: Ubuntu app launcher

**Files:**
- Create: `scripts/launch.sh`
- Create: `scripts/install-desktop.sh`
- Create: `invoice-creator.desktop.in`
- Create: `assets/icon.png`

- [ ] **Step 1: Create `scripts/launch.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDFILE="$ROOT/.server.pid"
PORT=8000
URL="http://127.0.0.1:$PORT"

cd "$ROOT"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  xdg-open "$URL" >/dev/null 2>&1 &
  exit 0
fi

if curl -sf "$URL" >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 &
  exit 0
fi

uv run uvicorn app.main:app --host 127.0.0.1 --port "$PORT" &
echo $! > "$PIDFILE"

for i in $(seq 1 30); do
  if curl -sf "$URL" >/dev/null 2>&1; then
    xdg-open "$URL" >/dev/null 2>&1 &
    exit 0
  fi
  sleep 0.5
done

echo "Invoice Creator failed to start on $URL" >&2
exit 1
```

Run: `chmod +x scripts/launch.sh`

- [ ] **Step 2: Create `invoice-creator.desktop.in`**

```ini
[Desktop Entry]
Name=Invoice Creator
Comment=Generate monthly PDF invoices
Exec=@INSTALL_ROOT@/scripts/launch.sh
Icon=@INSTALL_ROOT@/assets/icon.png
Type=Application
Categories=Office;Finance;
Terminal=false
StartupNotify=true
```

- [ ] **Step 3: Create `scripts/install-desktop.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/invoice-creator.desktop"

mkdir -p "$DESKTOP_DIR"
sed "s|@INSTALL_ROOT@|$ROOT|g" "$ROOT/invoice-creator.desktop.in" > "$DESKTOP_FILE"
chmod +x "$ROOT/scripts/launch.sh"
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
echo "Installed: $DESKTOP_FILE"
```

Run: `chmod +x scripts/install-desktop.sh`

- [ ] **Step 4: Add icon**

Create or copy a simple 256×256 PNG to `assets/icon.png` (document/invoice icon).

- [ ] **Step 5: Install and test**

Run: `./scripts/install-desktop.sh`
Launch from Ubuntu app menu — browser should open to the app.

- [ ] **Step 6: Commit**

```bash
git add scripts/ invoice-creator.desktop.in assets/icon.png
git commit -m "feat: add Ubuntu desktop launcher and install script"
```

---

### Task 9: README and final verification

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

Include:
- Prerequisites (Python 3.11+, uv, WeasyPrint system deps: `libpango`, `libcairo` on Ubuntu)
- Install: `uv sync --extra dev`
- Desktop install: `./scripts/install-desktop.sh`
- Dev run: `uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- First-time setup flow
- Monthly workflow

Ubuntu WeasyPrint deps:
```bash
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
```

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS

- [ ] **Step 3: End-to-end manual checklist**

- [ ] Settings saved with real data (EUR amount, USDT wallet, parties)
- [ ] Generate invoice for current month with 0 off days
- [ ] PDF matches Google Doc layout (visual compare)
- [ ] State file shows incremented invoice number
- [ ] Generate again with 1 off day — vacation totals update
- [ ] App launches from Ubuntu menu

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```

---

## Spec Coverage Checklist

### Functional spec (`2026-07-04-invoice-creator-design.md`)

| Requirement | Task |
|-------------|------|
| PDF generated directly | Task 5 |
| Local web form | Task 6 |
| Auto-track invoice # + vacation | Tasks 3, 4, 6 |
| Fixed EUR amount | Tasks 2, 6 |
| USDT wallet on invoice | Tasks 2, 5 |
| Off days listed + totals updated | Tasks 4, 5, 6 |
| Ubuntu app launcher | Task 8 |
| Settings incomplete blocked | Task 4, 6 |
| Off days > remaining blocked | Task 4, 6 |
| Year rollover prompt | Task 7 |
| State updated only after PDF success | Task 6 |
| Preview before download | Task 6 |

### UI spec (`2026-07-04-invoice-creator-ui-design.md`)

| Requirement | Task |
|-------------|------|
| Paper invoice aesthetic (tokens, fonts) | Tasks 5, 6 |
| Live paper preview (Option 1 layout) | Task 6 |
| Shared CSS web + PDF parity | Task 5 (`invoice-document.css`) |
| Generate page interactions (off-day chips, month selector) | Task 6 |
| Settings page layout & sections | Task 6 |
| Year rollover banner styling | Task 7 |
| Responsive + reduced motion | Task 6 |
| frontend-design polish (within UI spec) | Tasks 5, 6 |

---

## Execution Handoff

Plan references both specs. **Start at Task 1** and open spec sections only when the task calls for them.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
