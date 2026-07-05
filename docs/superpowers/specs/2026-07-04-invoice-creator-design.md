# Invoice Creator — Design Spec

**Date:** 2026-07-04  
**Status:** Approved  
**Author:** Brainstorming session with Ramin Maazallahi

## Problem

Each month, Ramin manually opens a Google Doc invoice template, updates the invoice date (last day of month), increments the invoice number, sets the USDT wallet address, enters the invoice amount in EUR, lists any off days taken, updates vacation totals (used / carried over / remaining), and exports a PDF. This is repetitive and error-prone.

## Goal

A personal local tool that generates a PDF invoice matching the existing Google Doc layout, with a simple web form for monthly input and automatic tracking of invoice numbers and vacation balances. Launchable from the Ubuntu applications menu.

## Decisions Summary

| Decision | Choice |
|----------|--------|
| Output | PDF generated directly (Google Doc used as layout reference only) |
| Interface | Simple local web form (FastAPI + HTML) |
| State | Auto-track invoice number and vacation balances between months |
| Amount | Fixed monthly amount in **EUR** (stored in settings) |
| Payment | USDT TRC20 wallet address on invoice (not the currency of the amount) |
| Off days | List dates on invoice **and** update used/remaining vacation totals |
| Platform | Ubuntu desktop — app launcher icon, no autostart |
| UI polish | Deferred to implementation (frontend-design skill during build) |

## Approach

**Python + FastAPI + HTML template → PDF (WeasyPrint)**

Chosen over Puppeteer (heavier) and ReportLab programmatic layout (harder to match existing doc).

---

## Monthly Workflow

### One-time setup

1. Launch **Invoice Creator** from Ubuntu apps menu (or run manually during development).
2. Open **Settings** and save:
   - Fixed monthly amount (EUR)
   - USDT TRC20 wallet address
   - From / Billed-to details (name, email, company, locations)
   - Annual vacation entitlement
   - Carried-over vacation days
   - Seed invoice number (current: `2334974`)

### Each month (~1 minute)

1. Open app → **Generate Invoice**
2. Form pre-fills:
   - **Date** — last day of selected month (default: current month)
   - **Invoice number** — last number + 1
   - **Amount** — from settings (EUR, read-only)
   - **Wallet** — from settings (read-only)
   - **Vacation totals** — from saved state
3. User adds **off-day dates** taken this month (if any)
4. Click **Generate PDF**
5. App:
   - Lists off-day dates on the invoice
   - Adds off-day count to `used_this_year`
   - Recalculates `remaining`
   - Saves new invoice number and vacation state
   - Downloads PDF (e.g. `Invoice-2334975-July-2026.pdf`)

Optional: **Preview** before download.

---

## Architecture

```
┌─────────────────┐     HTTP      ┌──────────────────┐
│  Browser (form) │ ◄────────────► │  FastAPI server  │
│  Settings page  │               │  (127.0.0.1:8000)│
│  Generate page  │               └────────┬─────────┘
└─────────────────┘                        │
                                    ┌──────┴──────┐
                                    ▼             ▼
                              JSON files     Jinja2 HTML
                              (settings +    + WeasyPrint
                               state)              │
                                    └──────┬──────┘
                                           ▼
                                    Invoice PDF
```

### Components

| Component | Responsibility |
|-----------|----------------|
| **FastAPI app** | Serves pages, handles form submit, orchestrates PDF generation |
| **Settings store** | `data/settings.json` — amount (EUR), wallet, parties, annual entitlement |
| **State store** | `data/state.json` — last invoice number, vacation totals, generation history |
| **Invoice service** | Computes next invoice #, date, vacation math, builds invoice data object |
| **PDF renderer** | Jinja2 HTML template → WeasyPrint → PDF bytes |
| **Launch script** | Starts server, opens browser, used by `.desktop` entry |
| **Web UI** | Settings page + Generate page (HTML/CSS; polished during implementation) |

### Data flow on Generate

1. Load settings + state
2. Merge form input (off-day dates, month selection)
3. Validate (settings complete, off days ≤ remaining)
4. Render PDF
5. Update state (invoice #, vacation totals, append to history)
6. Return PDF as download

**Critical:** State is updated only after successful PDF generation.

---

## Data Model

### `data/settings.json`

```json
{
  "invoice_amount_eur": 5000,
  "usdt_wallet": "T...",
  "from": {
    "name": "Ramin Maazallahi",
    "email": "r.mazallahi-ext@initiative-crm.com",
    "location": "Mashad, Iran"
  },
  "billed_to": {
    "name": "Boris Clement",
    "company": "Initiative solutions",
    "location": "Valreas, France"
  },
  "annual_vacation_entitlement": 31
}
```

### `data/state.json`

```json
{
  "last_invoice_number": 2334974,
  "vacation": {
    "used_this_year": 6,
    "carried_over": 7,
    "remaining": 31
  },
  "year": 2026,
  "history": [
    {
      "invoice_number": 2334974,
      "date": "2026-06-30",
      "off_days": [],
      "pdf_filename": "Invoice-2334974-June-2026.pdf"
    }
  ]
}
```

### Vacation math

- **Remaining** = `carried_over` + `annual_vacation_entitlement` − `used_this_year`
- On generate with new off days:
  - Add count of off days to `used_this_year`
  - Recalculate `remaining`
  - List each off-day date on the invoice
- **Year rollover (January 1):** Detect new calendar year on first generate; prompt user to reset `used_this_year` to 0 and optionally set new `carried_over` from prior year's remaining

### Computed invoice fields

| Field | Source |
|-------|--------|
| Invoice number | `last_invoice_number + 1` |
| Date | Last calendar day of selected month |
| Amount | `settings.invoice_amount_eur` (displayed as €) |
| Wallet | `settings.usdt_wallet` (USDT TRC20) |
| Off days list | Form input for current month |
| Vacation block | Updated state values |

---

## PDF Layout

HTML/CSS template mirroring the existing Google Doc **Invoice Template**:

| Block | Content |
|-------|---------|
| Header | Invoice number, "Invoice" title, date |
| Parties | Billed to / From (two columns) |
| Line items | Description + amount in **EUR** (single row: monthly services) |
| Payment | Wallet ID (USDT TRC20) |
| Off days | Dates taken this month (if any) |
| Vacation | Used this year / Carried over / Remaining |

First implementation may require one visual comparison pass against the Google Doc to fine-tune spacing and typography.

Reference doc: [Invoice Template](https://docs.google.com/document/d/1nULnot6sVoE4B2OC-absihyQtEmL9eQ5tin3gxvsn8Q/edit)

---

## Web UI

### Generate page

- Month selector (default: current month)
- Invoice number (pre-filled, read-only)
- Amount in EUR (from settings, read-only)
- Wallet (from settings, read-only)
- Off-day dates: add/remove date fields
- Vacation summary (read-only, updates as off days are added)
- **Preview** and **Generate & Download PDF** buttons

### Settings page

- Invoice amount (EUR)
- USDT wallet address
- From / Billed-to fields
- Annual vacation entitlement
- Carried-over days
- Seed / override last invoice number

UI aesthetics deferred to implementation using the frontend-design skill.

---

## Ubuntu App Launcher

### Goal

Click icon in Ubuntu apps → server starts → browser opens. No terminal required.

### Implementation

1. **`scripts/launch.sh`**
   - Start FastAPI on `127.0.0.1:8000` if not already running
   - Wait for HTTP readiness
   - Open browser via `xdg-open http://127.0.0.1:8000`

2. **`~/.local/share/applications/invoice-creator.desktop`**
   - Installed by `scripts/install-desktop.sh`
   - Points to launch script and bundled icon

3. **`assets/icon.png`**
   - Simple invoice-themed icon

### Server lifecycle

- Bind to `127.0.0.1` only (local, not network-exposed)
- If server already running on port 8000, open browser only
- Optional v2: Quit control in app footer to stop server

### Development run

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Error Handling

| Situation | Behavior |
|-----------|----------|
| Settings incomplete | Block Generate; list missing fields |
| Off days > remaining | Block with message showing counts |
| Year rollover | Prompt to reset used days and adjust carried over |
| Duplicate invoice # | Guard against double-submit |
| PDF generation fails | Show error; do **not** update state |
| State file missing/corrupt | Fall back to settings seed; warn user |
| Port 8000 in use | Try alternate port or show clear error |

---

## Out of Scope (v1)

- Google Docs read/write integration (reference only)
- Multi-user or authentication
- Cloud hosting or remote access
- Autostart on login
- Automated test suite (manual smoke test sufficient)
- Email / send invoice to client

---

## Success Criteria

1. Monthly invoice generated in under 2 minutes with only off-day input (when nothing else changed)
2. PDF visually matches existing Google Doc template
3. Invoice number and vacation totals persist correctly across months
4. Launchable from Ubuntu applications menu without terminal
5. Failed PDF generation never corrupts state

---

## Next Step

After user approves this spec, invoke **writing-plans** skill to produce a detailed implementation plan.
