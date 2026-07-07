# Off-Day Month Calendar — Design Spec

**Date:** 2026-07-07  
**Status:** Approved (scope confirmed)  
**Parent spec:** `2026-07-04-invoice-creator-design.md` (behavior unchanged)  
**Scope:** Off days on Generate page only

---

## Overview

Replace the Generate page off-day entry flow (`<input type="date">` + “+ Add day” button) with an inline **month calendar** for the selected invoice month. Users click days to toggle off days instead of picking a date and confirming each add.

**Fidelity bar:** PDF output, Settings vacation numbers, and invoice document layout are unchanged. Only the Generate-page chrome for off-day editing changes.

---

## Problem

The current flow works but feels manual:
1. Open the native date picker
2. Choose a date
3. Click “+ Add day”
4. Repeat for each off day

Off days are already constrained to the invoice month via `min`/`max` on the date input, but the interaction is one-at-a-time and disconnected from the month context.

---

## Goals

| Goal | Detail |
|------|--------|
| Click-to-toggle | Select/deselect off days directly on a month grid |
| Month-scoped | Calendar shows only the invoice month from the month selector |
| Live vacation math | `#vacation-used` / `#vacation-remaining` update on toggle (same as today) |
| Same server contract | Form still posts `off_days` as repeated `YYYY-MM-DD` hidden inputs |
| PDF unchanged | Off days still render as plain date lines in `_invoice_body.html` |

## Non-goals

- Settings vacation number fields
- `datetime-local` or time-of-day selection
- Drag-and-drop or multi-month calendar
- Storing off days in a new data model
- PDF / `invoice-document.css` changes
- In-page invoice preview fidelity changes (chips remain chrome-only)

---

## UX design

### Layout (Generate page, inside `.invoice-editor`)

```
Off days this month
┌─────────────────────────────────────┐
│  Mon  Tue  Wed  Thu  Fri  Sat  Sun  │
│   1    2    3    4    5    6    7   │
│  ...                               │
│  28   29   30   31                 │
└─────────────────────────────────────┘
[chip] 3 July, 2026 ×   [chip] 10 July, 2026 ×
```

- **Calendar grid:** 7 columns (Mon–Sun or locale-consistent), rows for weeks in the selected month.
- **Day cell states:**
  - Default — clickable, shows day number
  - Selected — off day (highlighted, matches neobrutalist chrome)
  - Out-of-month padding — empty cells at start/end of grid (not clickable)
  - Disabled — when year-rollover banner blocks generate (same as today)
- **Chips:** Keep existing chip list below the calendar for clarity and remove-button affordance; calendar toggle and chips stay in sync.
- **Remove date input + “+ Add day”** — calendar replaces them.

### Interactions

| Action | Result |
|--------|--------|
| Click unselected day | Add off day (chip + hidden input) |
| Click selected day | Remove off day (chip + hidden input) |
| Click chip × | Remove off day; calendar deselects that day |
| Change invoice month | Page reloads (`?month=YYYY-MM`); off days not in new month are dropped |
| Submit form | Unchanged — `off_days=2026-07-03&off_days=2026-07-10` |

### Accessibility

- Calendar days are `<button type="button">` with `aria-pressed` for selected state
- `aria-label` per day: e.g. “3 July 2026, off day” / “3 July 2026, not selected”
- Keyboard: focusable day buttons; Enter/Space toggles (optional v1: click-only acceptable if buttons are focusable)

---

## Architecture

| File | Change |
|------|--------|
| `app/templates/generate.html` | Replace `#off-day-picker` + `#add-off-day` with `#off-day-calendar` container; keep `#off-day-list` chips |
| `static/generate.js` | Add calendar render + toggle logic; reuse `addOffDayChip`, `updateVacationSummary`, `getSelectedMonthBounds` |
| `static/styles.css` | `.off-day-calendar`, `.off-day-calendar-day`, selected/disabled states (chrome scope, not `.invoice-document`) |
| `app/main.py` | No change |
| `app/invoice_service.py` | No change |
| `tests/test_main.py` | Assert calendar markup present; date picker / add button absent |

### Data flow

```
month input change → GET /generate?month=YYYY-MM
server renders off_days for month → chips + calendar initial state
user toggles day → JS updates chips + hidden inputs
POST /generate → _parse_off_days() → validate → draft/PDF
```

### Month change behavior

When the user changes the invoice month, the page reloads. Off days from the previous month that fall outside the new month are **not** carried over (same effective behavior as today when switching months with a full reload).

---

## Approach chosen

**Inline month calendar (vanilla JS)** — no third-party date library.

| Alternative | Why not |
|-------------|---------|
| Keep native `<input type="date">` + auto-add on change | Still one-day-at-a-time; doesn’t show month context |
| Full calendar library (Flatpickr, etc.) | Extra dependency for a single-month grid |
| Vacation date journal | Out of scope |

---

## Error handling

- Server-side validation unchanged (`validate_generate`: off days ≤ remaining vacation days)
- On validation error re-render, calendar initializes from POSTed `off_days` (same as chips today)
- Duplicate day toggle: no-op (idempotent)

---

## Testing

| Test | Assert |
|------|--------|
| `test_generate_with_settings_renders_paper_preview` | `#off-day-calendar` (or equivalent) present; `#off-day-picker` absent |
| Existing off-day validation tests | Unchanged — server contract identical |
| Manual QA | Toggle days → vacation counts update; PDF lists off days; month change drops out-of-month dates |

---

## Success criteria

1. User can toggle off days by clicking days on a month calendar for the selected invoice month.
2. Chip list and hidden `off_days` inputs stay in sync with the calendar.
3. Vacation used/remaining updates live without page reload.
4. Preview PDF and download output unchanged.
5. No new npm/CDN dependencies.
