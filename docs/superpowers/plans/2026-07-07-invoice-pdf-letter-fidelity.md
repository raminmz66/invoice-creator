# Invoice PDF Letter Fidelity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the generated invoice PDF visually match the reference `expected.pdf` — US Letter page, a single clean bottom-anchored wave band, a small signature over the Total row, and reference vertical spacing.

**Architecture:** Layout/CSS-only fix. Fonts and image assets already match the reference. Switch the page to US Letter, position both wave PNGs absolutely at the page bottom (green in front of navy) as one full-bleed band, swap the signature to the uncropped `image3.png` sized small over the Total row, and restore roomy spacing. Preview and Download share `render_invoice_pdf()`, so both update together.

**Tech Stack:** FastAPI, Jinja2, WeasyPrint 69, pytest. Files: `static/invoice-document.css`, `app/templates/_invoice_body.html`, `tests/test_pdf_renderer.py`.

**Spec:** `docs/superpowers/specs/2026-07-07-invoice-pdf-letter-fidelity-design.md`

---

## Reference facts (from analysis)

- `expected.pdf`: US Letter, 612×792pt.
- Embedded images = repo assets: green wave `image1.png` (983×341), navy wave `image2.png` (789×384), signature `image3.png` (363×198). `footer-green.png`/`footer-navy.png` are the same dimensions as `image1`/`image2`.
- Fonts: Oswald-Bold (title), Nunito (body) — already bundled and correct.
- Footer = one wave band across the bottom ~22–26%: green peaks left, navy peaks right, they meet mid-page; navy fills the very bottom edge full-width, no white gaps.
- Signature = small diagonal mark over the `Total` / `€ 1500` row, right side.

## File structure

| File | Responsibility |
|------|----------------|
| `static/invoice-document.css` | Page size, layout, wave band, signature, spacing |
| `app/templates/_invoice_body.html` | Signature asset reference (`image3.png`) |
| `tests/test_pdf_renderer.py` | Assert Letter page, single page, reference assets/tokens |

## Verification method (used in Task 6)

```bash
cd /home/ramin/invoice-creator
.venv/bin/python -c "
from datetime import date
from app.models import InvoiceDraft, PartyInfo
from app.pdf_renderer import render_invoice_pdf
draft = InvoiceDraft(
    invoice_number=2334974, invoice_date=date(2026, 6, 30), amount_eur=1500,
    usdt_wallet='TCEvAY15PUDMrb5uu35F1EhG21u2RYHtoS',
    from_party=PartyInfo(name='Ramin Maazallahi', email='r.mazallahi-ext@initiative-crm.com', location='Mashad, Iran'),
    billed_to=PartyInfo(name='Boris Clement', company='Initiative solutions', location='Valreas, France'),
    off_days=[], vacation_used=6, vacation_carried_over=7, vacation_remaining=31, month_label='June 2026',
)
open('/tmp/fidelity-check.pdf','wb').write(render_invoice_pdf(draft))
"
pdfinfo /tmp/fidelity-check.pdf | grep -E 'Pages|Page size'
pdftoppm -png -r 150 /tmp/fidelity-check.pdf /tmp/fidelity-check
```

Compare `/tmp/fidelity-check-1.png` against `/tmp/expected-1.png` (render the reference once with `pdftoppm -png -r 150 ~/Desktop/expected.pdf /tmp/expected`).

**Tuning knobs** (adjust only in Task 6 if the render diverges):
- Wave band too tall/short → adjust `.footer-wave` `width` (e.g. `calc(100% + 200pt)` widens/flattens navy) or add explicit `height`.
- White gap at a page corner → increase negative `left`/`right` and `width`.
- Signature size/position → `.invoice-signature` `width`, `right`, `bottom`.
- Content crowding waves → `.invoice-document` `padding-bottom`.

---

## Task 1: Switch page to US Letter

**Files:**
- Modify: `static/invoice-document.css:30-33` (`@page`)
- Modify: `static/invoice-document.css:44-55` (`.invoice-document`)
- Test: `tests/test_pdf_renderer.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_pdf_renderer.py`:

```python
def test_pdf_is_single_letter_page(sample_draft):
    from weasyprint import HTML

    from app.pdf_renderer import PROJECT_ROOT, render_invoice_html

    doc = HTML(
        string=render_invoice_html(sample_draft),
        base_url=str(PROJECT_ROOT),
    ).render()
    assert len(doc.pages) == 1
    # US Letter = 8.5in x 11in = 816px x 1056px at 96 CSS dpi
    assert round(doc.pages[0].width) == 816
    assert round(doc.pages[0].height) == 1056
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_pdf_renderer.py::test_pdf_is_single_letter_page -v`
Expected: FAIL — page is A4 (595×842pt → 794×1123px), so width assertion fails.

- [ ] **Step 3: Change the `@page` rule**

Replace lines 30-33:

```css
@page {
  size: letter;
  margin: 0;
}
```

- [ ] **Step 4: Change `.invoice-document` to relative Letter box with bottom reserve**

Replace the `.invoice-document` block (lines 44-55):

```css
.invoice-document {
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
  width: 8.5in;
  min-height: 11in;
  padding: 60pt 72pt 190pt;
  background: var(--paper);
  color: var(--ink);
  font-family: Nunito, Arial, "Liberation Sans", Helvetica, sans-serif;
  font-size: 11pt;
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_pdf_renderer.py::test_pdf_is_single_letter_page -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add static/invoice-document.css tests/test_pdf_renderer.py
git commit -m "feat: render invoice PDF on US Letter page to match reference"
```

---

## Task 2: Rebuild footer as one bottom-anchored wave band

**Files:**
- Modify: `static/invoice-document.css:217-234` (`.invoice-footer`, `.footer-wave`, `.footer-wave-navy`)

- [ ] **Step 1: Replace the footer CSS block**

Replace lines 217-234 (`.invoice-footer` through the end of the file):

```css
.invoice-footer {
  position: static;
}

.footer-wave {
  position: absolute;
  left: -72pt;
  right: -72pt;
  bottom: 0;
  width: calc(100% + 144pt);
  height: auto;
  display: block;
}

.footer-wave-navy {
  z-index: 1;
}

.footer-wave-green {
  z-index: 2;
}
```

Rationale: both waves are absolutely positioned against `.invoice-document` (now `position: relative`). `left/right: -72pt` with `width: calc(100% + 144pt)` cancels the 72pt side padding so the band bleeds to both page edges (no white corners); `overflow: hidden` on the document clips any excess. Green (`z-index: 2`) paints over navy (`z-index: 1`), reproducing the green-left / navy-right band.

- [ ] **Step 2: Confirm the template classes exist**

Verify `app/templates/_invoice_body.html` `invoice_footer()` macro already emits both classes (no edit needed):

```html
<div class="invoice-footer" aria-hidden="true">
  <img class="footer-wave footer-wave-green" src="static/invoice/footer-green.png" alt="">
  <img class="footer-wave footer-wave-navy" src="static/invoice/footer-navy.png" alt="">
</div>
```

Expected: both `footer-wave-green` and `footer-wave-navy` classes are present. If missing, add them to the respective `<img>` tags.

- [ ] **Step 3: Run existing tests to confirm no regression**

Run: `.venv/bin/pytest tests/test_pdf_renderer.py -v`
Expected: PASS (all tests, including the Letter test from Task 1).

- [ ] **Step 4: Commit**

```bash
git add static/invoice-document.css app/templates/_invoice_body.html
git commit -m "feat: pin footer waves as one bottom-anchored full-bleed band"
```

---

## Task 3: Signature — uncropped asset, small, over the Total row

**Files:**
- Modify: `app/templates/_invoice_body.html:43` (signature `<img src>`)
- Modify: `static/invoice-document.css:171-179` (`.invoice-signature`)
- Test: `tests/test_pdf_renderer.py:64-74` (`test_pdf_html_uses_reference_assets`)

- [ ] **Step 1: Update the asset assertion test**

In `tests/test_pdf_renderer.py`, change the signature assertions in `test_pdf_html_uses_reference_assets`:

```python
    assert "static/invoice/footer-green.png" in html
    assert "static/invoice/footer-navy.png" in html
    assert "static/invoice/image3.png" in html
    assert "static/invoice/signature.png" not in html
    assert "invoice-signature.svg" not in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_pdf_renderer.py::test_pdf_html_uses_reference_assets -v`
Expected: FAIL — template still references `signature.png`, not `image3.png`.

- [ ] **Step 3: Swap the signature asset in the template**

In `app/templates/_invoice_body.html`, change the signature image (line 43) from:

```html
  <img class="invoice-signature" src="static/invoice/signature.png" alt="">
```

to:

```html
  <img class="invoice-signature" src="static/invoice/image3.png" alt="">
```

- [ ] **Step 4: Resize/reposition the signature CSS**

Replace `.invoice-signature` (lines 171-179):

```css
.invoice-signature {
  position: absolute;
  right: 0;
  bottom: -18pt;
  width: 130pt;
  height: auto;
  pointer-events: none;
  z-index: 3;
}
```

Also revert the earlier tune on `.items-wrap` if present — it must be the clean version (lines 111-114):

```css
.items-wrap {
  position: relative;
  margin: 0 0 1.5em;
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_pdf_renderer.py::test_pdf_html_uses_reference_assets -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add static/invoice-document.css app/templates/_invoice_body.html tests/test_pdf_renderer.py
git commit -m "feat: place small uncropped signature over the Total row"
```

---

## Task 4: Restore reference vertical spacing

**Files:**
- Modify: `static/invoice-document.css` — `.invoice-date` (73-77), `.parties-table` (87-92), `.wallet` (181-184), `.section-title` (186-189)

- [ ] **Step 1: Widen the gaps to match the reference rhythm**

Apply these margin changes (keep every other property in each rule unchanged):

`.invoice-date` — change `margin`:

```css
.invoice-date {
  margin: 0 0 1.75em;
  font-size: 11pt;
  line-height: 1.15;
}
```

`.parties-table` — change `margin`:

```css
.parties-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 2.75em;
  table-layout: fixed;
}
```

`.wallet` — change `margin`:

```css
.wallet {
  margin: 0.5em 0 2em;
  line-height: 1.15;
}
```

`.section-title` — change top `margin`:

```css
.section-title {
  margin: 1.75em 0 0.5em;
  font-size: 12pt;
}
```

- [ ] **Step 2: Run tests to confirm no regression**

Run: `.venv/bin/pytest tests/test_pdf_renderer.py -v`
Expected: PASS (all tests).

- [ ] **Step 3: Commit**

```bash
git add static/invoice-document.css
git commit -m "feat: restore reference vertical spacing in invoice PDF"
```

---

## Task 5: Update CSS token test for Letter

**Files:**
- Modify: `tests/test_pdf_renderer.py:51-61` (`test_invoice_document_css_uses_reference_tokens`)

- [ ] **Step 1: Add Letter-page assertions to the token test**

Append inside `test_invoice_document_css_uses_reference_tokens`, after the existing asserts:

```python
    assert "size: letter" in lowered
    assert "8.5in" in lowered
```

- [ ] **Step 2: Run the test**

Run: `.venv/bin/pytest tests/test_pdf_renderer.py::test_invoice_document_css_uses_reference_tokens -v`
Expected: PASS (Task 1 already added `size: letter` and `8.5in`).

- [ ] **Step 3: Commit**

```bash
git add tests/test_pdf_renderer.py
git commit -m "test: assert Letter page tokens in invoice CSS"
```

---

## Task 6: Visual verification and tuning

**Files:**
- Modify (only if tuning needed): `static/invoice-document.css`

- [ ] **Step 1: Render the reference and the current output**

```bash
cd /home/ramin/invoice-creator
pdftoppm -png -r 150 ~/Desktop/expected.pdf /tmp/expected
.venv/bin/python -c "
from datetime import date
from app.models import InvoiceDraft, PartyInfo
from app.pdf_renderer import render_invoice_pdf
draft = InvoiceDraft(
    invoice_number=2334974, invoice_date=date(2026, 6, 30), amount_eur=1500,
    usdt_wallet='TCEvAY15PUDMrb5uu35F1EhG21u2RYHtoS',
    from_party=PartyInfo(name='Ramin Maazallahi', email='r.mazallahi-ext@initiative-crm.com', location='Mashad, Iran'),
    billed_to=PartyInfo(name='Boris Clement', company='Initiative solutions', location='Valreas, France'),
    off_days=[], vacation_used=6, vacation_carried_over=7, vacation_remaining=31, month_label='June 2026',
)
open('/tmp/fidelity-check.pdf','wb').write(render_invoice_pdf(draft))
"
pdfinfo /tmp/fidelity-check.pdf | grep -E 'Pages|Page size'
pdftoppm -png -r 150 /tmp/fidelity-check.pdf /tmp/fidelity-check
```

Expected: `Pages: 1`, `Page size: 612 x 792 pts (letter)`.

- [ ] **Step 2: Compare the two renders**

Read `/tmp/fidelity-check-1.png` and `/tmp/expected-1.png` side by side. Confirm the success criteria:
1. Footer is one wave band (green left, navy right, meeting mid-page), full-bleed, no white corners, ~22–26% page height.
2. Signature is small and diagonal over the Total / `€ 1500` row.
3. Vertical spacing matches the reference rhythm (content fills top ~70%).

- [ ] **Step 3: Tune if needed**

If any criterion fails, adjust only the relevant knob (see "Tuning knobs" above), re-run Step 1, and re-compare. Repeat until the render matches. Do not change fonts, colors, or assets.

- [ ] **Step 4: Verify no white gap at the page bottom corners**

```bash
.venv/bin/python -c "
from PIL import Image
im = Image.open('/tmp/fidelity-check-1.png'); w, h = im.size
white = sum(1 for x in range(w) for y in range(h-5, h)
            if im.getpixel((x, y))[:3] > (240, 240, 240))
print('white pixels in bottom 5 rows:', white, '/', w*5)
"
```

Expected: near 0 white pixels (navy fills the bottom edge).

- [ ] **Step 5: Run the full test suite**

Run: `.venv/bin/pytest`
Expected: all tests PASS.

- [ ] **Step 6: Commit any tuning changes**

```bash
git add static/invoice-document.css
git commit -m "fix: tune wave band and signature to match reference render"
```

(If no tuning was needed, skip this commit.)

---

## Self-review notes

- **Spec coverage:** Letter page (Task 1), wave band (Task 2), signature (Task 3), spacing (Task 4), test updates (Tasks 1/3/5), single-page + visual verify (Task 6). All spec sections covered.
- **Assets:** `footer-green.png`/`footer-navy.png` retained for waves (same dims as `image1`/`image2`); signature uses `image3.png`. `signature.png` no longer referenced.
- **Post-deploy:** User must restart uvicorn (port 8001) to pick up template/CSS changes — not automated here.
