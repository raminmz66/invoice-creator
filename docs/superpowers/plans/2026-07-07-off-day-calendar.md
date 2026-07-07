# Off-Day Month Calendar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Generate page date input + “+ Add day” flow with a click-to-toggle month calendar for off days, keeping the same form POST contract and PDF output.

**Architecture:** Vanilla JS month grid in `static/generate.js` renders inside `#off-day-calendar` in `generate.html`. Day clicks call existing `addOffDayChip` / new `removeOffDayChip`; chips and hidden `off_days` inputs stay the source of truth for form submit. Chrome styles in `styles.css` only — no PDF or server changes.

**Tech Stack:** FastAPI, Jinja2, vanilla JS, pytest TestClient. Spec: `docs/superpowers/specs/2026-07-07-off-day-calendar-design.md`

---

## File structure

| File | Responsibility |
|------|----------------|
| `app/templates/generate.html` | Calendar container markup; remove date picker + add button |
| `static/generate.js` | Render month grid, toggle days, sync with chips |
| `static/styles.css` | Calendar grid chrome (neobrutalist, outside `.invoice-document`) |
| `tests/test_main.py` | Assert calendar present; old picker absent |

---

## Task 1: Update Generate page test for calendar markup

**Files:**
- Modify: `tests/test_main.py:170-181`
- Test: `tests/test_main.py`

- [ ] **Step 1: Update `test_generate_with_settings_renders_paper_preview`**

Replace the assertions block with:

```python
def test_generate_with_settings_renders_paper_preview(client, seeded_data):
    response = client.get("/generate?month=2026-07")
    assert response.status_code == 200
    assert "invoice-document" in response.text
    assert "parties-table" in response.text
    assert "items-header" in response.text
    assert "Payment for July 2026" in response.text
    assert "Professional services" not in response.text
    assert "invoice-editor" in response.text
    assert 'id="off-day-calendar"' in response.text
    assert 'id="off-day-picker"' not in response.text
    assert 'id="add-off-day"' not in response.text
    assert "off-day-list" in response.text
    assert "2334975" in response.text
    assert "/static/generate.js" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_main.py::test_generate_with_settings_renders_paper_preview -v`

Expected: FAIL — `off-day-calendar` not in response; `off-day-picker` still present.

- [ ] **Step 3: Commit test-only change (optional) or proceed to Task 2 before commit**

Tests and template land together in Task 2 commit if preferred; minimum is red test before green.

---

## Task 2: Replace date picker with calendar container in template

**Files:**
- Modify: `app/templates/generate.html:49-63`

- [ ] **Step 1: Replace off-day actions block**

In `app/templates/generate.html`, replace the `.off-day-actions` block (lines 60-63) and keep list above it. The editor section becomes:

```html
      <div class="invoice-editor">
        <div class="section-title">Off days this month</div>
        <div id="off-day-calendar" class="off-day-calendar" aria-label="Off days this month"></div>
        <div id="off-day-list" class="off-day-list">
          {% for off_day in off_days %}
          <div class="off-day-chip" data-date="{{ off_day.isoformat() }}">
            <span>{{ off_day | format_date }}</span>
            <button type="button" class="chip-remove" aria-label="Remove {{ off_day | format_date }}">×</button>
            <input type="hidden" name="off_days" value="{{ off_day.isoformat() }}">
          </div>
          {% endfor %}
        </div>
      </div>
```

Remove entirely:
```html
        <div class="off-day-actions">
          <input id="off-day-picker" class="chrome-input chrome-input-compact" type="date" aria-label="Add off day">
          <button type="button" id="add-off-day" class="btn btn-outline btn-small">+ Add day</button>
        </div>
```

- [ ] **Step 2: Run test — still fails until JS renders calendar id (markup id is enough)**

Run: `.venv/bin/pytest tests/test_main.py::test_generate_with_settings_renders_paper_preview -v`

Expected: PASS (empty `#off-day-calendar` div satisfies `id="off-day-calendar"`).

- [ ] **Step 3: Commit**

```bash
git add app/templates/generate.html tests/test_main.py
git commit -m "feat: add off-day calendar container on Generate page"
```

---

## Task 3: Implement month calendar in generate.js

**Files:**
- Modify: `static/generate.js`

- [ ] **Step 1: Add helper functions after `formatDisplayDate`**

Insert before `addOffDayChip`:

```javascript
function getSelectedOffDays() {
  return Array.from(document.querySelectorAll("#off-day-list .off-day-chip")).map(
    (chip) => chip.dataset.date,
  );
}

function isOffDay(isoDate) {
  return Boolean(document.querySelector(`#off-day-list .off-day-chip[data-date="${isoDate}"]`));
}

function setCalendarDaySelected(isoDate, selected) {
  const button = document.querySelector(
    `#off-day-calendar .off-day-calendar-day[data-date="${isoDate}"]`,
  );
  if (!button) {
    return;
  }
  button.classList.toggle("is-selected", selected);
  button.setAttribute("aria-pressed", selected ? "true" : "false");
  const label = formatDisplayDate(isoDate);
  button.setAttribute("aria-label", selected ? `${label}, off day` : `${label}, not selected`);
}

function removeOffDayChip(isoDate) {
  document.querySelector(`#off-day-list .off-day-chip[data-date="${isoDate}"]`)?.remove();
  setCalendarDaySelected(isoDate, false);
  updateVacationSummary();
}

function toggleOffDay(isoDate) {
  if (isOffDay(isoDate)) {
    removeOffDayChip(isoDate);
  } else {
    addOffDayChip(isoDate);
    setCalendarDaySelected(isoDate, true);
  }
}

function buildMonthGrid(year, month) {
  const firstOfMonth = new Date(year, month - 1, 1);
  const lastDay = new Date(year, month, 0).getDate();
  // Monday = 0 … Sunday = 6
  const startOffset = (firstOfMonth.getDay() + 6) % 7;
  const pad = (value) => String(value).padStart(2, "0");
  const cells = [];

  for (let i = 0; i < startOffset; i += 1) {
    cells.push({ type: "pad" });
  }
  for (let day = 1; day <= lastDay; day += 1) {
    cells.push({ type: "day", isoDate: `${year}-${pad(month)}-${pad(day)}`, day });
  }
  while (cells.length % 7 !== 0) {
    cells.push({ type: "pad" });
  }
  return cells;
}

function renderOffDayCalendar() {
  const calendar = document.getElementById("off-day-calendar");
  const monthInput = document.getElementById("month");
  if (!calendar || !monthInput?.value) {
    return;
  }

  const [year, month] = monthInput.value.split("-").map(Number);
  const selected = new Set(getSelectedOffDays());
  const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const grid = document.createElement("div");
  grid.className = "off-day-calendar-grid";
  grid.setAttribute("role", "grid");

  const header = document.createElement("div");
  header.className = "off-day-calendar-row off-day-calendar-header";
  weekdays.forEach((name) => {
    const cell = document.createElement("div");
    cell.className = "off-day-calendar-head";
    cell.setAttribute("role", "columnheader");
    cell.textContent = name;
    header.appendChild(cell);
  });
  grid.appendChild(header);

  const body = document.createElement("div");
  body.className = "off-day-calendar-body";
  body.setAttribute("role", "rowgroup");

  const row = document.createElement("div");
  row.className = "off-day-calendar-row";
  row.setAttribute("role", "row");

  buildMonthGrid(year, month).forEach((cell) => {
    if (cell.type === "pad") {
      const pad = document.createElement("div");
      pad.className = "off-day-calendar-pad";
      pad.setAttribute("role", "gridcell");
      row.appendChild(pad);
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "off-day-calendar-day";
    button.dataset.date = cell.isoDate;
    button.setAttribute("role", "gridcell");
    button.textContent = String(cell.day);
    const isSelected = selected.has(cell.isoDate);
    button.classList.toggle("is-selected", isSelected);
    button.setAttribute("aria-pressed", isSelected ? "true" : "false");
    const label = formatDisplayDate(cell.isoDate);
    button.setAttribute("aria-label", isSelected ? `${label}, off day` : `${label}, not selected`);
    button.addEventListener("click", () => toggleOffDay(cell.isoDate));
    row.appendChild(button);
  });

  body.appendChild(row);
  grid.appendChild(body);
  calendar.replaceChildren(grid);
}
```

- [ ] **Step 2: Update `addOffDayChip` remove handler**

Change the remove button listener inside `addOffDayChip` from:

```javascript
  removeButton.addEventListener("click", () => {
    chip.remove();
    updateVacationSummary();
  });
```

to:

```javascript
  removeButton.addEventListener("click", () => {
    removeOffDayChip(isoDate);
  });
```

- [ ] **Step 3: Replace `DOMContentLoaded` handler**

Replace the entire `document.addEventListener("DOMContentLoaded", () => { ... });` block with:

```javascript
document.addEventListener("DOMContentLoaded", () => {
  const monthInput = document.getElementById("month");

  if (monthInput) {
    monthInput.addEventListener("change", () => {
      const url = new URL(window.location.href);
      url.searchParams.set("month", monthInput.value);
      window.location.href = url.toString();
    });
  }

  renderOffDayCalendar();
  updateVacationSummary();

  document.querySelectorAll(".chip-remove").forEach((button) => {
    button.addEventListener("click", () => {
      const chip = button.closest(".off-day-chip");
      if (chip?.dataset.date) {
        removeOffDayChip(chip.dataset.date);
      }
    });
  });
});
```

- [ ] **Step 4: Manual smoke test**

1. Start server, open `/generate?month=2026-07`
2. Click day 3 → chip appears, day highlighted, vacation counts update
3. Click day 3 again → chip removed, highlight cleared
4. Click chip × → same deselect on calendar
5. Preview PDF → off day listed

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest tests/test_main.py -v`

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add static/generate.js
git commit -m "feat: render click-to-toggle off-day month calendar"
```

---

## Task 4: Add calendar styles

**Files:**
- Modify: `static/styles.css` (after `.off-day-list` block, ~line 226)

- [ ] **Step 1: Add calendar CSS**

Insert after `.off-day-list { ... }`:

```css
.off-day-calendar {
  margin: 0.75rem 0;
}

.off-day-calendar-grid {
  display: grid;
  gap: 0.35rem;
}

.off-day-calendar-row {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.35rem;
}

.off-day-calendar-header {
  margin-bottom: 0.15rem;
}

.off-day-calendar-head {
  text-align: center;
  font-family: "Source Sans 3", Arial, sans-serif;
  font-size: 11px;
  font-weight: 700;
  color: var(--chrome-ink-muted);
  text-transform: uppercase;
}

.off-day-calendar-pad {
  min-height: 2rem;
}

.off-day-calendar-day {
  min-height: 2rem;
  border: 2px solid var(--chrome-border);
  border-radius: var(--chrome-radius);
  background: var(--chrome-input-bg);
  box-shadow: 2px 2px var(--chrome-border);
  color: var(--chrome-ink);
  font-family: "Source Sans 3", Arial, sans-serif;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
}

.off-day-calendar-day:hover {
  background: #fff;
}

.off-day-calendar-day.is-selected {
  background: var(--chrome-accent, #96ee71);
  color: var(--chrome-ink);
}

.off-day-calendar-day:active {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px var(--chrome-border);
}
```

- [ ] **Step 2: Remove unused `.off-day-actions` rules** (lines 257-262) if nothing else references them.

- [ ] **Step 3: Visual check** — calendar aligns with neobrutalist chips; selected days use green accent.

- [ ] **Step 4: Run full test suite**

Run: `.venv/bin/pytest -v`

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add static/styles.css
git commit -m "feat: style off-day month calendar on Generate page"
```

---

## Task 5: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Confirm server contract unchanged**

POST still sends `off_days=YYYY-MM-DD` repeated fields. Run:

```bash
.venv/bin/pytest tests/test_invoice_service.py tests/test_main.py::test_generate_preview_returns_pdf -v
```

Expected: PASS.

- [ ] **Step 2: Confirm PDF still excludes chrome**

Run: `.venv/bin/pytest tests/test_pdf_renderer.py::test_pdf_html_uses_reference_assets -v`

Expected: PASS — `off-day-chip` not in PDF HTML.

- [ ] **Step 3: Manual month-change check**

Change month selector from July to June → page reloads; July off days not carried over.

---

## Self-review notes

- **Spec coverage:** Click-to-toggle (Task 3), month-scoped grid (Task 3 `buildMonthGrid`), live vacation math (reuses `updateVacationSummary`), same POST contract (chips + hidden inputs), PDF unchanged (no template/CSS PDF changes), accessibility (`aria-pressed`, `aria-label`), chips kept (Task 2), no new dependencies.
- **Year-rollover disabled state:** Spec mentions disabled when rollover blocks generate. Buttons on preview/download are already `disabled` via template; calendar remains interactive for viewing — matches current off-day picker behavior. No extra work unless product asks to disable calendar clicks too.
- **Monday-first week:** Matches `en-GB` date formatting used elsewhere.
