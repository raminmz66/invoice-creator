# Invoice Creator — Roadmap

**Last updated:** 2026-07-05  
**Remote:** `git@github.com:raminmz66/invoice-creator.git` (private) · tracks `origin/main`  
**Resume here:** See [Current status](#current-status) and [Session handoff](#session-handoff)

---

## Delivery workflow

Each task follows this cycle — **do not skip steps**:

```
Implement task → commit locally → STOP for user review
       ↓
User approves → git push origin main → update roadmap → start next task
       ↓
User requests changes → fix → commit → STOP for review again (no push until approved)
```

| Step | Who | Action |
|------|-----|--------|
| 1 | Agent | Implement task per plan |
| 2 | Agent | Commit locally with clear message |
| 3 | Agent | Update this roadmap; **stop** and notify user |
| 4 | User | Review diff / test locally |
| 5 | User | Reply **Approved** (or request changes) |
| 6 | Agent | `git push origin main` |
| 7 | Agent | Start next task |

**Push rule:** Never push to remote until the user explicitly approves the task.

---

## Reference docs

| Doc | Path | Purpose |
|-----|------|---------|
| **Roadmap** (this file) | `docs/superpowers/ROADMAP.md` | Progress, notes, where to continue |
| **Implementation plan** | `docs/superpowers/plans/2026-07-04-invoice-creator.md` | Task steps, files, code |
| **Functional spec** | `docs/superpowers/specs/2026-07-04-invoice-creator-design.md` | Behavior, data, errors |
| **UI spec** | `docs/superpowers/specs/2026-07-04-invoice-creator-ui-design.md` | Visual design, layouts |
| **UI skill** | `.agents/skills/frontend-design/SKILL.md` | Polish during Tasks 5–6 |
| **Python style** | `.agents/skills/python-code-style/SKILL.md` | Linting, types, docstrings |
| **FastAPI** | `.agents/skills/fastapi-python/SKILL.md` | Pydantic models, routes (Tasks 3–6) |

**Conflict rule:** Functional spec → behavior. UI spec → appearance. Plan → build order.

---

## Task tracker

| # | Task | Status | Review |
|---|------|--------|--------|
| 1 | Project scaffold | ✅ Done | ✅ Approved · pushed |
| 2 | Data models | ✅ Done | ✅ Approved · pushed |
| 3 | Storage layer | ✅ Done | ✅ Approved · pushed |
| 4 | Invoice service | ✅ Done | ⏳ Pending |
| 5 | PDF renderer | ⬜ Not started | — |
| 6 | FastAPI + web UI | ⬜ Not started | — |
| 7 | Year rollover | ⬜ Not started | — |
| 8 | Ubuntu launcher | ⬜ Not started | — |
| 9 | README + smoke test | ⬜ Not started | — |

**Legend:** ⬜ Not started · 🔄 In progress · ✅ Done · ⏳ Awaiting user review

---

## Current status

**Active task:** None — awaiting review of Task 4  
**Next action after approval:** `git push origin main` → Task 5 — PDF renderer  
**Remote:** `origin` → `git@github.com:raminmz66/invoice-creator.git` (SSH)  
**Blockers:** None

**Bootstrap push (2026-07-05):** Initial commits pushed during remote setup (`fee4020`, `8592ad5`). From Task 2 onward, push only after user approval.

---

## Task log

### Task 1: Project scaffold
- **Plan section:** `2026-07-04-invoice-creator.md` → Task 1
- **Deliverables:** `pyproject.toml`, `.gitignore`, `app/__init__.py`, `data/.gitkeep`, `tests/__init__.py`, `.venv` via `uv sync`
- **Verified:** `uv sync --extra dev` OK (44 packages); `uv run pytest --co -q` → no tests yet (expected)
- **Completed:** 2026-07-05
- **Notes:** Added `[tool.hatch.build.targets.wheel]` so hatchling packages `app` correctly. Pushed: `fee4020`–`456cdee`.

### Task 2: Data models
- **Plan section:** `2026-07-04-invoice-creator.md` → Task 2
- **Deliverables:** `app/models.py`, `data/settings.example.json`, `data/state.example.json`
- **Verified:** Example JSON parses into `Settings` and `AppState` via Pydantic
- **Completed:** 2026-07-05
- **Commit:** `9ca9265` → revised in follow-up commits (local, not pushed)
- **Notes:** Reviewed with `python-code-style` + `fastapi-python` skills. Added ConfigDict, Field constraints/descriptions, module docstrings, ruff config, `tests/test_models.py` (5 tests).

### Task 3: Storage layer
- **Plan section:** `2026-07-04-invoice-creator.md` → Task 3
- **Deliverables:** `app/storage.py`, `tests/test_storage.py`
- **Verified:** 4 storage tests pass; settings JSON uses `"from"` alias
- **Completed:** 2026-07-05
- **Commit:** local, not pushed
- **Notes:** Loads/saves `data/settings.json` and `data/state.json`

### Task 4: Invoice service
- **Plan section:** `2026-07-04-invoice-creator.md` → Task 4
- **Deliverables:** `app/invoice_service.py`, `tests/test_invoice_service.py`
- **Verified:** 16/16 tests pass (7 invoice service tests)
- **Completed:** 2026-07-05
- **Commit:** local, not pushed
- **Notes:** Vacation math, draft building, validation, state updates, PDF filename

### Task 5: PDF renderer
- **Specs:** UI spec (tokens, PDF parity) + functional spec (PDF layout)
- **Notes:** —

### Task 6: FastAPI + web UI
- **Specs:** UI spec (full) + frontend-design skill
- **Notes:** —

### Task 7: Year rollover
- **Notes:** —

### Task 8: Ubuntu launcher
- **Notes:** —

### Task 9: README + smoke test
- **Notes:** —

---

## Session handoff

**For a new chat/session**, tell the agent:

> Continue Invoice Creator from `docs/superpowers/ROADMAP.md`. Follow the [Delivery workflow](#delivery-workflow): push only after user approval. Check current status before starting the next task.

**Dev commands** (after Task 1):

```bash
cd /home/ramin/invoice-creator
uv sync --extra dev
uv run pytest -v
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000  # after Task 6
```

**Project root:** `/home/ramin/invoice-creator`

---

## User review gate

After each task, the agent **must stop** and wait for:

- ✅ **Approved** — push to `origin main`, then start next task  
- 🔄 **Changes requested** — fix, commit, update roadmap, re-submit for review (no push)  
- ⏸️ **Pause** — stop until user returns
