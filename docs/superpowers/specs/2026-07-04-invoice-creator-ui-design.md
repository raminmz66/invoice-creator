# Invoice Creator — UI/UX Design Spec

**Date:** 2026-07-04  
**Status:** Draft — pending user review  
**Parent spec:** `2026-07-04-invoice-creator-design.md`  
**Aesthetic direction:** A — Paper invoice (live paper preview, Option 1)

---

## Overview

A local monthly invoice tool that looks and feels like a document on a desk — not a SaaS dashboard. The Generate page is WYSIWYG: the A4 paper card on screen matches the exported PDF. Settings uses the same visual language on a narrower form card.

**Reference sites:**
- [EvryTools Serif template](https://evrytools.com/tools/invoice-generator)
- [1nvoic3 Classic template](https://1nvoic3.com/templates/classic)

---

## Design tokens

### Color palette

| Token | Hex | Use |
|-------|-----|-----|
| `--desk` | `#EDEAE3` | App background (area around paper) |
| `--paper` | `#F7F4EE` | Paper card + PDF background |
| `--paper-shadow` | `#E8E4DC` | Paper card shadow |
| `--ink` | `#2C2C2C` | Primary text |
| `--ink-muted` | `#6B6560` | Labels, secondary text |
| `--rule` | `#D4CFC6` | Hairlines, table borders |
| `--accent` | `#3D4F5F` | Links, focus, primary button (muted navy) |
| `--accent-hover` | `#2E3D4A` | Button hover |
| `--danger` | `#8B4513` | Validation errors (warm, on-paper) |
| `--field-bg` | `#FFFCF7` | Editable input backgrounds |

### Typography

| Role | Font | Size | Weight |
|------|------|------|--------|
| Invoice title | Cormorant Garamond | 28px | 500 |
| Amount | Cormorant Garamond | 20px | 500 |
| Body / labels | Source Sans 3 | 13–14px | 400 |
| App chrome | Source Sans 3 | 14px | 400 |

**Google Fonts import:** `Cormorant+Garamond:wght@500;600` + `Source+Sans+3:wght@400;500`

### Layout constants

| Token | Value |
|-------|-------|
| Paper max-width | 210mm (A4) |
| Paper padding | 2.5cm |
| Settings card max-width | 640px |
| Paper border-radius | 0 |
| Input/button border-radius | 4px |
| Paper shadow | `0 2px 8px rgba(44, 44, 44, 0.08), 0 1px 2px rgba(44, 44, 44, 0.06)` |

### Signature element

The **A4 paper card** is the hero. App chrome stays minimal; the invoice document is the focal point.

---

## Global chrome

### Top bar

- Height: 48px, background `--desk`
- Left: "Invoice Creator" in Source Sans 3, 14px, `--ink-muted`
- Right: contextual nav link — "Settings →" on Generate, "← Generate" on Settings
- No logo, no sidebar, no hamburger menu

---

## Generate page (`/` or `/generate`)

### Layout

1. Top bar
2. Month selector (above paper, centered): `Invoice for: [July 2026 ▾]`
3. A4 paper card (centered)
4. Action buttons below paper (centered): Preview PDF | Generate & Download
5. Optional year-rollover banner above paper when applicable

### Paper card content (top to bottom)

| Block | Content | Editable |
|-------|---------|----------|
| Meta | `No. {invoice_number}` | No |
| Title | `Invoice` | No |
| Date | `Date: {last day of selected month}` | No (derived from month selector) |
| Parties | Billed to / From two columns | No (from Settings) |
| Line items | Single row: "Professional services — {Month YYYY}" + € amount | No |
| Payment | Wallet ID (USDT TRC20) + address | No |
| Off days | Section title + date chips + "+ Add day" | **Yes** |
| Vacation | Used / Carried over / Remaining | No (live-updates from off days) |

### Month selector

- Dropdown or native `<input type="month">` styled to match paper aesthetic
- Changing month updates invoice date to last calendar day of that month
- Default: current month

### Off-day interaction

1. Click **"+ Add day"** → date picker (constrained to selected month)
2. Date appears as chip: `{d} {Month}, {YYYY} [×]`
3. Vacation used/remaining update immediately (client-side)
4. Remove via **×** on chip

### Action buttons

| Button | Variant | Behavior |
|--------|---------|----------|
| Preview PDF | Outlined (`--accent` border, transparent bg) | Opens PDF in new tab; **no state change** |
| Generate & Download | Filled (`--accent` bg, white text) | Validate → PDF → download → save state |

### Validation

- Inline message below off-days section, `--danger` color
- Example: *"You have 1 day remaining but added 2 off days."*
- Block Generate until resolved

### Year rollover banner

Shown when `state.year != selected year`:

> **New year detected.** Confirm vacation reset before generating.  
> ☐ Reset used days to 0 · Carried over: [input] days · [Apply]

### First-run / incomplete settings

Replace paper card with centered message:

> **Set up your invoice details first.**  
> [Go to Settings]

---

## Settings page (`/settings`)

### Layout

- Same top bar + desk background
- Narrower paper card (640px max), titled **"Invoice details"**
- Sections separated by hairline rules (`--rule`)

### Sections & fields

**Payment**
- Monthly amount (EUR) — number input, `€` prefix
- USDT wallet (TRC20) — text input, monospace optional

**Your details (From)**
- Name, Email, Location

**Client (Billed to)**
- Name, Company, Location

**Vacation & invoice tracking**
- Annual entitlement (days)
- Carried over days
- Used this year (days)
- Last invoice number
- Remaining (computed, read-only): *"Remaining: {n} days"*

### Interactions

- **Save settings** — primary button, bottom-right of card
- Success toast: *"Settings saved"* — fades after 2s
- First save creates `state.json` from vacation seed fields
- Remaining recalculates live on entitlement / carried over / used change

### Copy guidelines

- Sentence case labels
- Plain verbs: "Save settings", "Add day", "Generate & Download"
- No jargon: "Monthly amount (EUR)" not "Invoice Amount Configuration"

---

## PDF parity

The web paper card and `invoice_pdf.html` template **share the same CSS token values** where possible:

| Property | Web + PDF |
|----------|-----------|
| Background | `--paper` |
| Fonts | Cormorant Garamond + Source Sans 3 (WeasyPrint must load fonts) |
| Padding | 2.5cm |
| Party layout | Two-column table |
| Line item table | Hairline borders `--rule` |
| Amount format | `€5,000.00` |

Implementation: extract shared invoice styles to `static/invoice-document.css` imported by both web template and PDF template.

---

## Responsive behavior

| Breakpoint | Behavior |
|------------|----------|
| ≥768px | Paper centered, full A4 width up to 210mm |
| <768px | Paper fills width with 16px side margin; padding reduced to 1.5cm; party columns stack vertically |
| <480px | Month selector full-width; buttons stack vertically (Preview above Generate) |

Desktop-first (primary use: Ubuntu app launcher on laptop). Mobile is supported but not optimized for thumb-heavy interaction.

---

## Motion & accessibility

### Motion

- Paper card: fade-in on load (200ms) — optional, subtle
- Toast: fade in/out (150ms)
- No scroll animations, no parallax
- **`prefers-reduced-motion: reduce`:** disable all transitions

### Accessibility

- Visible focus rings: 2px `--accent` outline on all interactive elements
- Off-day chips: remove button has `aria-label="Remove 3 July 2026"`
- Form labels: visually hidden but present for screen readers on Settings
- Color contrast: `--ink` on `--paper` ≥ 7:1; `--accent` buttons ≥ 4.5:1
- Date picker: native `<input type="date">` for keyboard/accessibility

---

## Component inventory

| Component | Used on |
|-----------|---------|
| `TopBar` | Both pages |
| `PaperCard` | Both pages (variant: a4 / narrow) |
| `MonthSelector` | Generate |
| `OffDayChip` | Generate |
| `VacationSummary` | Generate (read-only block) |
| `InlineError` | Generate |
| `YearRolloverBanner` | Generate (conditional) |
| `SettingsForm` | Settings |
| `Toast` | Settings (save success) |
| `Button` (primary / outline) | Both |

Implementation note: these can be Jinja2 partials/macros, not a JS framework.

---

## Out of scope (UI v1)

- Dark mode
- Invoice history page
- Drag-and-drop off-day calendar
- Custom logo upload
- Animations beyond fade-in/toast
- Mobile-native app shell

---

## Success criteria (UI)

1. Generate page visually matches exported PDF (side-by-side compare passes)
2. Monthly workflow requires interaction with only month selector + off days
3. App feels like a document tool, not a generic web form
4. Settings completable in under 3 minutes on first run
5. Readable and usable at 1280×800 (typical laptop)

---

## Implementation notes

- Apply **frontend-design** skill (`.agents/skills/frontend-design/SKILL.md`) during CSS/HTML build
- Shared CSS between web preview and PDF is critical for WYSIWYG promise
- Reference Google Doc for final spacing tune: [Invoice Template](https://docs.google.com/document/d/1nULnot6sVoE4B2OC-absihyQtEmL9eQ5tin3gxvsn8Q/edit)
