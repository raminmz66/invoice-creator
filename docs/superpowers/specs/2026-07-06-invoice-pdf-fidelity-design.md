# Invoice PDF Fidelity — Design Spec

**Date:** 2026-07-06  
**Status:** Approved  
**Parent spec:** `2026-07-04-invoice-creator-design.md` (behavior unchanged)  
**Related:** `2026-07-06-invoice-creator-ui-redesign.md` (chrome + in-page preview; this spec wins for PDF output fidelity)

---

## Overview

Match the exported PDF to the user's Google Doc invoice template (provided as `InvoiceTemplate.html` + PNG assets). Preview PDF (new tab) and Generate & Download must produce identical output. Settings page and Generate form chrome are out of scope and stay as-is. The in-page HTML card on Generate is not a fidelity target — it remains for off-day editing only.

**Approach:** Reference-faithful rebuild — bundle Oswald/Nunito fonts and reference PNG assets; rebuild PDF template and `invoice-document.css` to mirror the Google Doc export structure and extracted style values.

---

## Goals

| Goal | Detail |
|------|--------|
| PDF matches reference | Layout, fonts, colors, spacing, signature, footer waves |
| Preview = export | Both use `render_invoice_pdf()` — no separate code paths |
| Real preview | Preview PDF button opens actual WeasyPrint output (already true; improve output quality) |
| No chrome changes | Settings + Generate controls unchanged |
| Off-day editor unchanged | In-page card markup not updated for PDF parity |

## Non-goals

- In-page HTML invoice card matching the PDF
- Embedded PDF iframe on the Generate page
- Settings or neobrutalist chrome redesign
- Pixel-perfect automated diff tooling
- Adopting Google Doc HTML class soup verbatim

---

## Reference source

Google Doc export (`InvoiceTemplate.html`) defines:

| Element | Reference value |
|---------|-----------------|
| Page padding | `72pt` (`.c8`) |
| Title | Oswald, 48pt, bold |
| Body / labels | Nunito, 11–12pt |
| Table header bg | `#96EE71` |
| Table borders | `#E9C119`, 1pt solid |
| Footer navy | `#0D2B2E` (image2) |
| Parties | Tab-aligned two columns |
| Items table | 4 columns: Item (wide) \| spacer \| Total \| Amount |
| Signature | `image3.png` overlaid on total row |
| Footer | `image1.png` (green wave) + `image2.png` (navy wave) |
| Amount | `€ 1500` — space after €, no decimals for whole numbers |

---

## Design tokens (`invoice-document.css`)

| Token | Value | Use |
|-------|-------|-----|
| `--paper` | `#FFFFFF` | Page background |
| `--ink` | `#000000` | All text |
| `--invoice-green` | `#96EE71` | Table header row |
| `--invoice-gold` | `#E9C119` | Table cell borders |
| `--invoice-navy` | `#0D2B2E` | Footer wave (reference) |

**Typography**

| Role | Font | Size | Weight |
|------|------|------|--------|
| Title "Invoice" | Oswald | 48pt | 700 |
| Body text | Nunito | 11pt | 400 |
| Bold labels | Nunito | 11–12pt | 700 |
| Invoice number | Nunito | 12pt | 700 |

**Layout**

| Property | Value |
|----------|-------|
| Page size | A4 (`210mm × 297mm`) |
| `@page margin` | `0` |
| Content padding | `72pt` all sides; extra bottom padding for footer images |
| Table cell padding | `5pt` |
| Body line-height | `1.15` |
| Table cell line-height | `1.0` |

---

## Fonts & assets

### Fonts (local, no CDN)

Store under `static/fonts/`:

- `Oswald-Bold.woff2` — title
- `Nunito-Regular.woff2` — body
- `Nunito-Bold.woff2` — labels, invoice number, total row

Declare via `@font-face` in `invoice-document.css`. WeasyPrint resolves fonts through `base_url` in `pdf_renderer.py` (`PROJECT_ROOT`).

Fallback stacks: `Nunito, Arial, Liberation Sans, sans-serif` (body); `Oswald, Arial, sans-serif` (title).

### Images (from reference zip)

Store under `static/invoice/`:

| File | Use |
|------|-----|
| `image1.png` | Green footer wave (top) |
| `image2.png` | Navy footer wave (bottom) |
| `image3.png` | Signature overlay on total row |

PDF template uses **relative** paths (`static/invoice/image3.png`) — not `/static/...` absolute URLs — so WeasyPrint resolves them via `base_url`.

Remove `invoice-signature.svg` and inline SVG footer once PNGs are wired.

---

## PDF layout (`_invoice_body.html`)

Single source of truth for PDF content. Structure mirrors reference blocks:

| Block | Implementation |
|-------|----------------|
| Invoice no. | Right-aligned, Nunito 12pt bold |
| Title | "Invoice", Oswald 48pt bold |
| Date | Bold `Date:` + spacing + formatted date |
| Parties | Two columns with fixed widths matching tab alignment |
| Line items | 4-column table; green header row; gold borders on data/total rows |
| Item row | `Payment for {month_label}` \| empty \| empty \| `€ {amount}` |
| Total row | empty \| empty \| **Total** \| **€ {amount}** |
| Signature | `image3.png`, absolutely positioned over total area |
| Wallet | Bold label line, address on next line |
| Off days | Plain indented lines when present (PDF only) |
| Vacation | Tab/column-aligned used / carried / remaining |
| Footer | Stacked PNGs, full-width, absolute bottom |

**Amount format:** Existing `format_eur_invoice` filter — `€ 1500` for whole numbers, `€ 1 500.50` for decimals (space after €).

**Date format:** Existing `format_date` filter — `30 June, 2026`.

---

## Preview & download pipeline

No architectural change. Both paths call `render_invoice_pdf(draft)`:

| Entry | Route | Disposition |
|-------|-------|-------------|
| Preview PDF button | POST `/generate` `action=preview` | `inline` (new tab) |
| Download button | POST `/generate` `action=download` | `attachment` |
| Direct preview | GET `/generate/preview` | `inline` |

**Rules:**

- `invoice_pdf.html` imports `invoice-document.css` only
- No chrome classes in PDF HTML (`off-day-chip`, `chrome-*`, `btn-*`)
- `generate.html` in-page card is **not** updated in this work

---

## File changes

| File | Action |
|------|--------|
| `static/fonts/Oswald-Bold.woff2` | Add |
| `static/fonts/Nunito-Regular.woff2` | Add |
| `static/fonts/Nunito-Bold.woff2` | Add |
| `static/invoice/image1.png` | Add (from reference zip) |
| `static/invoice/image2.png` | Add (from reference zip) |
| `static/invoice/image3.png` | Add (from reference zip) |
| `static/invoice-document.css` | Rewrite tokens, fonts, layout |
| `app/templates/_invoice_body.html` | Rebuild structure for reference fidelity |
| `static/invoice-signature.svg` | Remove (replaced by image3) |
| `tests/test_pdf_renderer.py` | Extend assertions |
| `generate.html` | No change |
| `styles.css` | No change |

---

## Testing

### Manual

1. Export reference PDF from Google Doc with sample June 2026 data.
2. Generate app PDF with matching settings.
3. Side-by-side compare: title font, green header, gold borders, parties, signature, footer waves, vacation spacing.
4. Confirm Preview PDF tab matches downloaded file.
5. Confirm off-day editor on Generate page still works.

### Automated (`test_pdf_renderer.py`)

| Test | Assertion |
|------|-----------|
| `test_render_pdf_produces_bytes` | Unchanged — `%PDF` header, size > 1KB |
| CSS fidelity | Oswald/Nunito `@font-face`, `#96ee71`, `#e9c119`; no `googleapis` |
| HTML fidelity | Contains `static/invoice/image3.png`, footer images; no chrome classes |
| Amount format | `format_eur_invoice(1500)` → `1500`; rendered HTML has `€ 1500` |

---

## Success criteria

1. App PDF and Google Doc export visually match at a glance.
2. Preview PDF and downloaded PDF are identical.
3. Settings and Generate chrome unchanged.
4. Off-day editing on Generate page still works.
5. All existing tests pass.

---

## Implementation notes

- Download Oswald and Nunito `.woff2` files from Google Fonts (SIL Open Font License) rather than relying on CDN in the PDF path.
- Copy PNG assets from the user-provided `Invoice Template.zip`.
- Tune party column widths and signature position in a compare pass against the reference PDF screenshot.
- Prior UI redesign spec (`2026-07-06-invoice-creator-ui-redesign.md`) specified Arial for invoice text; **this spec supersedes that for PDF output** in favor of Oswald/Nunito from the reference export.
