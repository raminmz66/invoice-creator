# Invoice Creator — UI Redesign Spec

**Date:** 2026-07-06  
**Status:** Pending user review  
**Supersedes (partial):** `2026-07-04-invoice-creator-ui-design.md` — invoice document tokens and typography; app chrome direction  
**Parent spec:** `2026-07-04-invoice-creator-design.md` (behavior unchanged)

---

## Overview

Split visual redesign with two independent aesthetics:

1. **Invoice paper + PDF** — Match the user's Google Doc template as closely as possible (plain, white, Arial, tab-aligned layout).
2. **App chrome** — Neobrutalist form styling adapted from [Uiverse by ayyjayy2](https://uiverse.io) (thick borders, offset shadows, beige/light-blue inputs).

The Generate page combines both: bold controls around a faithful document preview. Settings uses chrome only.

**Approach:** Strict CSS split (recommended in brainstorm). Optional visual tune pass using a Google Doc PDF export as reference.

---

## Design tokens

### Invoice document (`invoice-document.css` only)

| Token | Value | Use |
|-------|-------|-----|
| `--paper` | `#FFFFFF` | Page background (web + PDF) |
| `--ink` | `#000000` or `#323232` | Body text (tune to match Doc export) |
| `--ink-muted` | `#666666` | Secondary text if needed |
| `--rule` | `#CCCCCC` | Table borders (tune to Doc) |

**Typography**

| Role | Font | Size | Weight |
|------|------|------|--------|
| All invoice text | Arial, Liberation Sans, Helvetica, sans-serif | 11pt | 400 |
| Labels (`Billed to:`, section titles) | Same | 11pt | 400 or 700 (match Doc) |
| Amount in table | Same | 11pt | 400 |

**Removed from invoice:** Cormorant Garamond, cream paper (`#F7F4EE`), serif title styling.

**Layout constants**

| Token | Value |
|-------|-------|
| Paper max-width | 210mm (A4) |
| Paper padding | Match Google Doc export (default 2.5cm, tune in compare pass) |
| Party layout | Two-column table (not flexbox) |
| Vacation block | Tab-aligned or fixed-width columns matching Doc |

### App chrome (`styles.css` only)

| Token | Value | Use |
|-------|-------|-----|
| `--desk` | `#EDEAE3` | Page background around cards |
| `--chrome-bg` | `#B8D4E8` | Settings / alert card fill (softened lightblue) |
| `--chrome-input-bg` | `#F5F5DC` | Input and chip fill (beige) |
| `--chrome-ink` | `#323232` | Primary text |
| `--chrome-ink-muted` | `#666666` | Labels |
| `--chrome-border` | `#000000` | 2px borders |
| `--chrome-shadow` | `4px 4px #000000` | Offset box-shadow |
| `--chrome-focus` | `#2d8cf0` | Input focus border |
| `--chrome-radius` | `5px` | Inputs, buttons, cards |
| `--danger` | `#8B4513` | Validation errors (unchanged) |

**Chrome typography:** Source Sans 3 or system sans for app UI only. Never applied inside `.invoice-document`.

---

## Invoice document layout (Google Doc fidelity)

Target structure from [Invoice Template](https://docs.google.com/document/d/1nULnot6sVoE4B2OC-absihyQtEmL9eQ5tin3gxvsn8Q/edit):

| Block | Content | Styling |
|-------|---------|---------|
| Meta | `No. {invoice_number}` | Plain line, same font as body |
| Title | `Invoice` | Plain line (not large serif) |
| Date | `Date: {d Month, YYYY}` | Single line; colon spacing per Doc |
| Parties | `Billed to:` / `From:` header row, then name / company-or-email / location per column | Two-column table, Doc alignment |
| Line items | `Description` \| `Amount` table; one row for monthly services | Light borders per Doc |
| Wallet | `Wallet ID (USDT TRC20):` then address on next line | Bold label optional if Doc uses bold |
| Off days | `Off days this month:` + date lines (PDF only when present) | Plain indented or list lines |
| Vacation | `Vacations (and Off days):` then used / carried / remaining | Tab or column alignment per Doc |

**Date format:** `30 June, 2026` (existing `format_date` filter).

**Amount format:** `€5,000.00` (existing `format_eur` filter).

---

## App chrome components

| Component | Pages | Pattern |
|-----------|-------|---------|
| `TopBar` | Both | Minimal desk bar; nav link only |
| `ChromeCard` | Settings, empty state | Uiverse `.form`: border, offset shadow, padding |
| `ChromeInput` | Settings, Generate | Uiverse `.input`: 40px height, shadow, focus ring |
| `ChromeButton` primary | Settings save, Generate download | Uiverse `.button-confirm` |
| `ChromeButton` outline | Preview, Apply | Same border/shadow, beige/transparent fill |
| `OffDayChip` | Generate | Small neobrutalist pill; not in PDF |
| `MonthSelector` | Generate | Chrome-styled `<input type="month">` |
| `YearRolloverBanner` | Generate | Chrome alert card |
| `Toast` | Settings | Neobrutalist bottom-right card |
| `InlineError` | Generate, Settings | `--danger` text below controls |

**Interaction:** `:active` on buttons — `transform: translate(3px, 3px)` and shadow collapse (from Uiverse). Disabled: reduced opacity, `cursor: not-allowed`.

**Scope rule:** Selectors for chrome tokens and Uiverse patterns must not target `.invoice-document` or its descendants except `.off-day-chip` and off-day editor controls (`.off-day-actions`, `#off-day-picker`).

---

## Generate page layout

```
Top bar (desk)
  → Month selector (chrome)
  → Year rollover banner (chrome, conditional)
  → Inline errors (chrome, conditional)
  → .paper-card (subtle shadow only)
      → .invoice-document (Google Doc — white, plain)
          → static invoice fields
          → off-day chips (chrome classes)
          → off-day add controls (chrome)
          → vacation summary (doc typography)
  → Action buttons (chrome)
```

**Rules**

1. `.paper-card` wrapper: white invoice area; subtle drop shadow on web only — no black offset shadow on the document.
2. PDF template (`invoice_pdf.html`) uses `.invoice-document` only — no `.paper-card`, no chrome.
3. Off days in PDF: plain date lines via `{% for off_day %}`; no chip markup.
4. Year rollover: Generate/Preview buttons disabled until Apply; chrome disabled styling.
5. Month change reloads page; vacation math unchanged (client-side JS).

---

## Settings page layout

- Desk background + narrow `ChromeCard` (max-width 640px).
- Sections: Payment / From / Billed to / Vacation & tracking — separated by hairline rules or spacing within chrome card.
- Save button bottom-right; toast on success.
- No invoice document block.

---

## PDF parity & WeasyPrint

| Concern | Rule |
|---------|------|
| Stylesheets | PDF imports `invoice-document.css` only |
| Fonts | Arial / Liberation Sans / Helvetica — no Google Fonts CDN in PDF path |
| Layout | Table-based columns in invoice body |
| Shadows | No box-shadow on PDF invoice content |
| Chrome bleed | PDF HTML must not contain `button-confirm`, `off-day-chip`, `chrome-` classes |
| Compare pass | Export Google Doc PDF + app PDF for same month; tune CSS until match |

---

## Responsive & accessibility

| Breakpoint | Behavior |
|------------|----------|
| ≥768px | Invoice centered, full A4 width up to 210mm |
| <768px | Invoice full width with margin; party columns stack if needed for readability |
| <480px | Month selector and buttons stack full-width |

- Visible focus: 2px `--chrome-focus` on chrome inputs/buttons.
- Chip remove: `aria-label="Remove {date}"`.
- `prefers-reduced-motion: reduce`: disable translate/shadow animations on chrome.
- Invoice contrast: black/dark text on white ≥ 7:1.

---

## Out of scope

- Dark mode
- Invoice history page
- Neobrutalism on invoice document body
- Google Doc chrome matching (Settings stays Uiverse)
- Logo upload
- Drag-and-drop calendar for off days
- React / component framework migration

---

## Success criteria

1. App PDF and Google Doc export visually match at a glance.
2. Web `.invoice-document` preview matches downloaded PDF (except off-day chip chrome).
3. Settings and Generate controls use neobrutalist styling per Uiverse reference.
4. No neobrutalist styles inside invoice PDF output.
5. All existing tests pass; PDF generation smoke test passes.

## Testing

**Manual**

- Settings form, toast, inputs match Uiverse pattern
- Generate controls (month, chips, buttons, banner) match chrome
- Invoice preview white/Arial, matches Doc layout
- Side-by-side PDF compare with Google Doc export
- Off days: chips on web, plain lines in PDF

**Automated**

- Assert rendered PDF HTML excludes chrome class names
- Assert `invoice-document.css` does not reference Cormorant or fonts.googleapis.com
- Existing `test_render_pdf_produces_bytes` unchanged

---

## Implementation notes

- Update `static/invoice-document.css` and `app/templates/invoice_pdf.html` for Doc fidelity.
- Update `static/styles.css` with scoped chrome tokens; refactor Settings/Generate markup class names as needed.
- Keep `generate.html` paper card structure; split chip styles from doc typography.
- Apply `frontend-design` skill only to chrome polish; invoice follows Doc literally.
- Parent UI spec (`2026-07-04-invoice-creator-ui-design.md`) remains reference for workflow/copy; this spec wins for visual tokens and typography where they conflict.
