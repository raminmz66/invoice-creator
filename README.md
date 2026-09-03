# Invoice Creator

Local web app for generating monthly PDF invoices with automatic invoice-number and vacation-day tracking.

## Prerequisites

Only the WeasyPrint system libraries have to be installed by hand — they are the
one dependency that needs `apt` (Ubuntu):

```bash
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1 libglib2.0-0
```

[uv](https://docs.astral.sh/uv/) and Python 3.11+ are **not** prerequisites: the
launcher installs uv if it is missing and `uv` then fetches a managed
interpreter, so the app runs even when your system Python is older.

## Install

```bash
git clone git@github.com:raminmz66/invoice-creator.git
cd invoice-creator
./scripts/bootstrap.sh
```

`bootstrap.sh` installs uv, a suitable Python and the locked dependencies. You can
skip it — the app launcher runs the same bootstrap on every start, so a fresh
clone works straight from the applications menu. Add `uv sync --extra dev` if you
want the dev tools (pytest, ruff).

## Ubuntu app launcher

Install a desktop entry so you can launch from the applications menu:

```bash
./scripts/install-desktop.sh
```

Click **Invoice Creator** in the app menu. The launcher:

1. Installs uv, Python and the locked dependencies if any are missing
2. Starts the FastAPI server if it is not already running
3. Opens your default browser to the app

Setup runs silently, so its output is appended to `.server.log`; failures also
raise a desktop notification telling you what to do.

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
