# Invoice Creator — Roadmap

**Last updated:** 2026-07-05  
**Workflow:** One task at a time → implement → **stop for user review** → next task  
**Resume here:** See [Current status](#current-status) and [Session handoff](#session-handoff)

---

## Reference docs

| Doc | Path | Purpose |
|-----|------|---------|
| **Roadmap** (this file) | `docs/superpowers/ROADMAP.md` | Progress, notes, where to continue |
| **Implementation plan** | `docs/superpowers/plans/2026-07-04-invoice-creator.md` | Task steps, files, code |
| **Functional spec** | `docs/superpowers/specs/2026-07-04-invoice-creator-design.md` | Behavior, data, errors |
| **UI spec** | `docs/superpowers/specs/2026-07-04-invoice-creator-ui-design.md` | Visual design, layouts |
| **UI skill** | `.agents/skills/frontend-design/SKILL.md` | Polish during Tasks 5–6 |

**Conflict rule:** Functional spec → behavior. UI spec → appearance. Plan → build order.

---

## Task tracker

| # | Task | Status | Review |
|---|------|--------|--------|
| 1 | Project scaffold | ✅ Done | ⏳ Pending |
| 2 | Data models | ⬜ Not started | — |
| 3 | Storage layer | ⬜ Not started | — |
| 4 | Invoice service | ⬜ Not started | — |
| 5 | PDF renderer | ⬜ Not started | — |
| 6 | FastAPI + web UI | ⬜ Not started | — |
| 7 | Year rollover | ⬜ Not started | — |
| 8 | Ubuntu launcher | ⬜ Not started | — |
| 9 | README + smoke test | ⬜ Not started | — |

**Legend:** ⬜ Not started · 🔄 In progress · ✅ Done · ⏳ Awaiting user review

---

## Current status

**Active task:** None — awaiting review of Task 1  
**Next action after approval:** Task 2 — Data models  
**Blockers:** None

---

## Task log

### Task 1: Project scaffold
- **Plan section:** `2026-07-04-invoice-creator.md` → Task 1
- **Deliverables:** `pyproject.toml`, `.gitignore`, `app/__init__.py`, `data/.gitkeep`, `tests/__init__.py`, `.venv` via `uv sync`
- **Verified:** `uv sync --extra dev` OK (44 packages); `uv run pytest --co -q` → no tests yet (expected)
- **Completed:** 2026-07-05
- **Notes:** Added `[tool.hatch.build.targets.wheel]` so hatchling packages `app` correctly. Commit skipped — user to request when ready.

### Task 2: Data models
- **Notes:** —

### Task 3: Storage layer
- **Notes:** —

### Task 4: Invoice service
- **Notes:** —

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

> Continue Invoice Creator from `docs/superpowers/ROADMAP.md`. Check current status, complete the active task if unfinished, or start the next task only if the previous one is ✅ and user-approved.

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

- ✅ Approved — proceed to next task  
- 🔄 Changes requested — fix, update roadmap, re-submit for review  
- ⏸️ Pause — stop until user returns
