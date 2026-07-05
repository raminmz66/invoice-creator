# Invoice Creator

Local web app for generating monthly PDF invoices with automatic invoice-number and vacation-day tracking.

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** package manager
- **WeasyPrint system libraries** (Ubuntu):

```bash
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
```

## Install

```bash
git clone git@github.com:raminmz66/invoice-creator.git
cd invoice-creator
uv sync --extra dev
```

## Ubuntu app launcher

Install a desktop entry so you can launch from the applications menu:

```bash
./scripts/install-desktop.sh
```

Click **Invoice Creator** in the app menu. The launcher:

1. Starts the FastAPI server if it is not already running
2. Opens your default browser to the app

If port 8000 is already in use by another app, the launcher automatically picks the next free port (8001–8010). The active port is stored in `.server.port`.

## Development run

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## First-time setup

1. Open **Settings** (`/settings`)
2. Fill in:
   - Monthly amount (EUR)
   - USDT wallet (TRC20)
   - Your details (From): name, email, location
   - Client (Billed to): name, company, location
   - Vacation tracking: annual entitlement, carried-over days, used this year, last invoice number
3. Click **Save settings**

Settings and state are stored in `data/settings.json` and `data/state.json` (created on first save; gitignored).

## Monthly workflow

1. Open **Generate** (`/generate`)
2. Select the invoice month
3. Add any off days for that month (optional)
4. Review the live paper preview and vacation totals
5. **Preview PDF** — opens PDF in a new tab without saving state
6. **Generate & Download** — downloads PDF and updates invoice number, vacation usage, and history

If you generate for a new calendar year, a banner prompts you to reset used days and set carried-over days before continuing.

## Tests

```bash
uv run pytest -v
```

## Project layout

```
app/           FastAPI app, models, business logic, PDF renderer
static/        App chrome + shared invoice document styles
data/          Runtime settings/state (examples committed)
scripts/       Desktop launcher and install script
tests/         pytest suite
```

## Specs

Design docs live in `docs/superpowers/`:

- Functional spec: `specs/2026-07-04-invoice-creator-design.md`
- UI spec: `specs/2026-07-04-invoice-creator-ui-design.md`
- Implementation plan: `plans/2026-07-04-invoice-creator.md`
