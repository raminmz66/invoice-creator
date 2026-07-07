# Invoice PDF Letter Fidelity — Design Spec

**Date:** 2026-07-07  
**Status:** Approved  
**Parent spec:** `2026-07-06-invoice-pdf-fidelity-design.md` (extends; corrects layout regressions)  
**Reference:** `~/Desktop/expected.pdf` (Google Doc export, ground truth) vs `~/Desktop/output.pdf` (current app output)

---

## Overview

The generated invoice PDF must visually match the reference `expected.pdf`. The current output diverges in page size, footer wave geometry, signature size/placement, and vertical spacing. This is a **layout/CSS problem only** — fonts and source image assets already match the reference.

**Fidelity bar:** Visually equivalent (same layout, spacing, wave band, signature placement — a person sees them as the same design). Not pixel-perfect; body text stays Nunito (reference mixes Arial + Nunito; that difference is out of scope).

**Approach:** CSS/template layout rewrite reusing existing assets (Approach A).

---

## Root cause

The reference and the app share the same fonts (Oswald-Bold, Nunito) and the same source images. `expected.pdf` embeds the exact green wave (983×341), navy wave (789×384), and signature (363×198) already present in the repo as `static/invoice/image1.png`, `image2.png`, `image3.png`.

Current CSS regressions:
1. Renders on **A4** instead of the reference **US Letter**.
2. Stacks the two wave PNGs **in-flow** with a `-52mm` negative-margin overlap and `calc(100% + 144pt)` width → produces tall blobby "hill" shapes (~45% of page) with white gaps at edges, instead of one clean bottom-anchored band (~22%).
3. Uses a **cropped, oversized** signature (`signature.png` 204×160 at `205pt`, `bottom: -55pt`) spanning From-email through the table, instead of the small diagonal mark over the Total row.
4. Compresses vertical spacing so content is cramped at the top.

---

## Findings (evidence)

| Aspect | Expected (reference) | Current output |
|--------|---------------------|----------------|
| Page size | US Letter 612×792pt | A4 595×842pt |
| Vertical rhythm | Roomy, content top→mid | Cramped at top |
| Footer band | One wave band, ~22% height, green-left/navy-right meeting mid-page, full-bleed | Blobby hills, ~45% height, white gaps at edges |
| Signature | Small diagonal over Total row | Large, spans From-email through table |
| Signature asset | `image3.png` 363×198 (full, transparent padding) | `signature.png` 204×160 (cropped) |
| Fonts | Oswald-Bold, Nunito, (Arial body) | Oswald-Bold, Nunito |

---

## Design

### 1. Page → US Letter
- `@page { size: letter; margin: 0 }`
- `.invoice-document`: width `216mm`, min-height `279mm` (8.5×11in), keep `72pt` side padding, reserve bottom space for the wave band.

### 2. Footer wave band
- Both wave PNGs `position: absolute; left: 0; right: 0; bottom: 0; width: 100%` — full-bleed, anchored to the physical page bottom.
- **Navy behind, green in front.** Green's peak shows on the left and tapers under the navy near mid-page; navy rises on the right and fills the bottom edge fully → reproduces the reference band.
- Remove the `-52mm` margin, `calc(100% + 144pt)` width, and navy `background` fill hacks.
- Resulting band height ≈ 22% of the page (reference proportion).

### 3. Signature
- Use uncropped `image3.png` (matches reference), placed `position: absolute` over the **Total** row, right-aligned near the amount column, small (~120pt wide), diagonal.
- Remove oversized `205pt` / `bottom: -55pt` / `padding-bottom: 50pt` values from the current tune.

### 4. Vertical spacing
- Restore reference rhythm: comfortable gaps after Date, the parties block, the items table, the wallet block, and the vacations block, so content fills the top ~75% and the waves occupy the bottom band.

### 5. Tests
- Update `tests/test_pdf_renderer.py`: assert Letter page dimensions and `image3.png` reference; keep asserting single-page output and reference tokens (colors, fonts, four-column table).

---

## Files to change

| File | Change |
|------|--------|
| `static/invoice-document.css` | Letter page, bottom-anchored full-bleed wave band, small signature, restored spacing |
| `app/templates/_invoice_body.html` | Swap signature asset to `image3.png`; footer image order if needed |
| `tests/test_pdf_renderer.py` | Letter page assertion, `image3.png` reference |

---

## Non-goals

- Pixel-perfect overlay match or automated diff tooling
- Adopting Arial for body text
- Regenerating/redrawing wave or signature assets
- In-page HTML preview on the Generate page
- Settings / chrome changes
- Server restart automation (user restarts uvicorn after deploy, as before)

---

## Success criteria

1. Generated PDF is US Letter and visually matches `expected.pdf`.
2. Footer is one clean wave band (green left, navy right, meeting mid-page), full-bleed with no white gaps, ~22% page height.
3. Signature is small and diagonal over the Total/amount row.
4. Vertical spacing matches the reference rhythm.
5. PDF remains single-page; all tests pass.
