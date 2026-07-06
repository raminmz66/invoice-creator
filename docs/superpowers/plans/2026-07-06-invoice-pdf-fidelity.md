# Invoice PDF Fidelity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Match exported invoice PDF to the Google Doc reference (Oswald/Nunito fonts, reference colors, 4-column table, PNG signature/footer) while keeping Preview PDF and Download identical via the existing WeasyPrint pipeline.

**Architecture:** Bundle fonts and PNG assets locally; rewrite `invoice-document.css` and `_invoice_body.html` to mirror the reference export. PDF-only changes — `generate.html` and chrome CSS stay untouched. `_invoice_body.html` remains the single PDF content source.

**Tech Stack:** Jinja2, WeasyPrint, static CSS, pytest

**Spec:** `docs/superpowers/specs/2026-07-06-invoice-pdf-fidelity-design.md`

---

## File map

| File | Responsibility |
|------|----------------|
| `static/fonts/*.ttf` | Oswald Bold + Nunito Regular/Bold for WeasyPrint |
| `static/invoice/image{1,2,3}.png` | Footer waves + signature from reference zip |
| `static/invoice-document.css` | All PDF layout tokens, `@font-face`, table/party/footer styles |
| `app/templates/_invoice_body.html` | PDF invoice markup (4-col table, PNG assets) |
| `app/templates/invoice_pdf.html` | Thin wrapper — unchanged except if CSS path needs tweak |
| `tests/test_pdf_renderer.py` | Fidelity assertions for HTML/CSS/PDF bytes |
| `static/invoice-signature.svg` | **Delete** — replaced by `image3.png` |

---

### Task 1: Add reference assets (fonts + images)

**Files:**
- Create: `static/fonts/Oswald-Bold.ttf`
- Create: `static/fonts/Nunito-Regular.ttf`
- Create: `static/fonts/Nunito-Bold.ttf`
- Create: `static/invoice/image1.png`
- Create: `static/invoice/image2.png`
- Create: `static/invoice/image3.png`

- [ ] **Step 1: Create directories**

```bash
mkdir -p static/fonts static/invoice
```

- [ ] **Step 2: Download fonts from Google Fonts GitHub (SIL OFL)**

```bash
curl -fsSL "https://github.com/google/fonts/raw/main/ofl/oswald/static/Oswald-Bold.ttf" \
  -o static/fonts/Oswald-Bold.ttf
curl -fsSL "https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-Regular.ttf" \
  -o static/fonts/Nunito-Regular.ttf
curl -fsSL "https://github.com/google/fonts/raw/main/ofl/nunito/static/Nunito-Bold.ttf" \
  -o static/fonts/Nunito-Bold.ttf
```

Expected: three `.ttf` files, each > 10 KB.

- [ ] **Step 3: Copy PNG assets from reference zip**

```bash
unzip -o "/home/ramin/Downloads/Invoice Template.zip" "images/*" -d /tmp/invoice-ref
cp /tmp/invoice-ref/images/image1.png static/invoice/
cp /tmp/invoice-ref/images/image2.png static/invoice/
cp /tmp/invoice-ref/images/image3.png static/invoice/
```

Expected: three PNG files in `static/invoice/`.

- [ ] **Step 4: Commit**

```bash
git add static/fonts/ static/invoice/
git commit -m "chore: add Oswald/Nunito fonts and reference invoice PNG assets"
```

---

### Task 2: Fidelity tests (write failing tests first)

**Files:**
- Modify: `tests/test_pdf_renderer.py`

- [ ] **Step 1: Add shared draft fixture and new tests**

Add at top of `tests/test_pdf_renderer.py` after imports:

```python
import pytest

@pytest.fixture
def sample_draft():
    return InvoiceDraft(
        invoice_number=2334974,
        invoice_date=date(2026, 6, 30),
        amount_eur=1500,
        usdt_wallet="TCEvAY15PUDMrb5uu35F1EhG21u2RYHtoS",
        from_party=PartyInfo(
            name="Ramin Maazallahi",
            email="r.mazallahi-ext@initiative-crm.com",
            location="Mashad, Iran",
        ),
        billed_to=PartyInfo(
            name="Boris Clement",
            company="Initiative solutions",
            location="Valreas, France",
        ),
        off_days=[],
        vacation_used=6,
        vacation_carried_over=7,
        vacation_remaining=31,
        month_label="June 2026",
    )
```

Add these test functions:

```python
def test_invoice_document_css_uses_reference_tokens():
    css = (Path(__file__).resolve().parent.parent / "static" / "invoice-document.css").read_text(encoding="utf-8")
    lowered = css.lower()
    assert "googleapis" not in lowered
    assert "cormorant" not in lowered
    assert "#96ee71" in lowered
    assert "#e9c119" in lowered
    assert "oswald" in lowered
    assert "nunito" in lowered
    assert "@font-face" in lowered


def test_pdf_html_uses_reference_assets(sample_draft):
    html = render_invoice_html(sample_draft)
    assert "static/invoice/image1.png" in html
    assert "static/invoice/image2.png" in html
    assert "static/invoice/image3.png" in html
    assert "invoice-signature.svg" not in html
    assert "footer-waves" not in html
    assert "off-day-chip" not in html
    assert "chrome-input" not in html
    assert "Payment for June 2026" in html
    assert "€ 1500" in html


def test_pdf_html_has_four_column_items_table(sample_draft):
    html = render_invoice_html(sample_draft)
    assert 'class="items"' in html
    assert "items-total" in html
    assert html.count("<td") >= 8  # header + data + total rows across 4 cols


def test_render_pdf_produces_bytes(sample_draft):
    pdf = render_invoice_pdf(sample_draft)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 5000
```

Remove the old duplicate `test_render_pdf_produces_bytes` and `test_invoice_document_css_is_doc_faithful` / `test_pdf_html_excludes_chrome_classes` if they overlap — keep one consolidated suite.

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/ramin/invoice-creator && pytest tests/test_pdf_renderer.py -v
```

Expected: FAIL on CSS tokens (`#96ee71`, Oswald/Nunito), HTML assets (`static/invoice/image3.png`), or SVG still present.

- [ ] **Step 3: Commit**

```bash
git add tests/test_pdf_renderer.py
git commit -m "test: add PDF fidelity assertions for reference template"
```

---

### Task 3: Rewrite `invoice-document.css`

**Files:**
- Modify: `static/invoice-document.css`

- [ ] **Step 1: Replace entire file with reference-faithful styles**

```css
@font-face {
  font-family: "Oswald";
  src: url("fonts/Oswald-Bold.ttf") format("truetype");
  font-weight: 700;
  font-style: normal;
}

@font-face {
  font-family: "Nunito";
  src: url("fonts/Nunito-Regular.ttf") format("truetype");
  font-weight: 400;
  font-style: normal;
}

@font-face {
  font-family: "Nunito";
  src: url("fonts/Nunito-Bold.ttf") format("truetype");
  font-weight: 700;
  font-style: normal;
}

:root {
  --paper: #ffffff;
  --ink: #000000;
  --invoice-green: #96ee71;
  --invoice-gold: #e9c119;
  --invoice-navy: #0d2b2e;
}

@page {
  size: A4;
  margin: 0;
}

body {
  font-family: Nunito, Arial, "Liberation Sans", Helvetica, sans-serif;
  font-size: 11pt;
  line-height: 1.15;
  color: var(--ink);
  background: var(--paper);
  margin: 0;
}

.invoice-document {
  box-sizing: border-box;
  position: relative;
  width: 210mm;
  min-height: 297mm;
  padding: 72pt 72pt 200pt;
  background: var(--paper);
  color: var(--ink);
  font-family: Nunito, Arial, "Liberation Sans", Helvetica, sans-serif;
  font-size: 11pt;
  overflow: hidden;
}

.invoice-no {
  margin: 0 0 0.5em;
  text-align: right;
  font-size: 12pt;
  font-weight: 700;
  font-family: Nunito, Arial, sans-serif;
}

.invoice-title {
  margin: 0 0 0.15em;
  font-family: Oswald, Arial, sans-serif;
  font-size: 48pt;
  font-weight: 700;
  line-height: 1;
}

.invoice-date {
  margin: 0 0 1em;
  font-size: 11pt;
  line-height: 1.15;
}

.label-bold,
.party-label,
.wallet-label,
.section-title,
.total-label {
  font-weight: 700;
}

.parties-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 1.5em;
  table-layout: fixed;
}

.parties-table td {
  width: 50%;
  vertical-align: top;
  padding: 0;
  line-height: 1.15;
}

.party-label {
  padding-bottom: 0.25em;
}

.party-line {
  margin: 0;
  padding: 0;
  line-height: 1.15;
}

.items-wrap {
  position: relative;
  margin: 0 0 1.5em;
}

table.items {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

table.items td {
  padding: 5pt;
  vertical-align: top;
  line-height: 1;
  border: none;
}

table.items tr.items-header td {
  background: var(--invoice-green);
  font-weight: 400;
  border-bottom: 0;
}

table.items tr.items-data td,
table.items tr.items-total td {
  border-top: 1pt solid var(--invoice-gold);
  border-bottom: 1pt solid var(--invoice-gold);
}

table.items td.col-item {
  width: 59%;
}

table.items td.col-spacer {
  width: 12%;
}

table.items td.col-total-label {
  width: 14%;
}

table.items td.col-amount {
  width: 15%;
  text-align: right;
  white-space: nowrap;
}

table.items tr.items-total td.col-total-label,
table.items tr.items-total td.col-amount {
  font-weight: 700;
}

.invoice-signature {
  position: absolute;
  right: 0;
  bottom: -10pt;
  width: 95pt;
  height: auto;
  pointer-events: none;
}

.wallet {
  margin: 0 0 1.25em;
  line-height: 1.15;
}

.section-title {
  margin: 1em 0 0.35em;
  font-size: 12pt;
}

.off-day {
  margin: 0.1em 0 0.1em 1.25em;
  line-height: 1.15;
}

.vacation-block {
  line-height: 1.15;
}

.vacation-line {
  margin: 0;
  padding: 0;
}

.vacation-line .vacation-value {
  display: inline-block;
  min-width: 12em;
}

.invoice-footer {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  line-height: 0;
}

.footer-wave {
  display: block;
  width: 100%;
  height: auto;
}
```

- [ ] **Step 2: Run CSS-related tests**

```bash
pytest tests/test_pdf_renderer.py::test_invoice_document_css_uses_reference_tokens -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add static/invoice-document.css
git commit -m "feat: restyle invoice-document.css to match Google Doc reference"
```

---

### Task 4: Rebuild `_invoice_body.html`

**Files:**
- Modify: `app/templates/_invoice_body.html`

- [ ] **Step 1: Replace template with 4-column table + PNG assets**

```html
{% macro invoice_top(draft) %}
<p class="invoice-no">No. {{ draft.invoice_number }}</p>
<p class="invoice-title">Invoice</p>
<p class="invoice-date"><span class="label-bold">Date:</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{{ draft.invoice_date | format_date }}</p>

<table class="parties-table">
  <tr>
    <td class="party-label">Billed to:</td>
    <td class="party-label">From:</td>
  </tr>
  <tr>
    <td class="party-line">{{ draft.billed_to.name }}</td>
    <td class="party-line">{{ draft.from_party.name }}</td>
  </tr>
  <tr>
    <td class="party-line">{{ draft.billed_to.company }}</td>
    <td class="party-line">{{ draft.from_party.email }}</td>
  </tr>
  <tr>
    <td class="party-line">{{ draft.billed_to.location }}</td>
    <td class="party-line">{{ draft.from_party.location }}</td>
  </tr>
</table>

<div class="items-wrap">
  <table class="items">
    <tr class="items-header">
      <td class="col-item" colspan="2">Item</td>
      <td class="col-spacer"></td>
      <td class="col-amount">Amount</td>
    </tr>
    <tr class="items-data">
      <td class="col-item" colspan="2">Payment for {{ draft.month_label }}</td>
      <td class="col-spacer"></td>
      <td class="col-amount">€ {{ draft.amount_eur | format_eur_invoice }}</td>
    </tr>
    <tr class="items-total">
      <td class="col-item" colspan="2"></td>
      <td class="col-total-label total-label">Total</td>
      <td class="col-amount">€ {{ draft.amount_eur | format_eur_invoice }}</td>
    </tr>
  </table>
  <img class="invoice-signature" src="static/invoice/image3.png" alt="">
</div>

<div class="wallet">
  <span class="wallet-label">Wallet ID (USDT TRC20):</span><br>
  {{ draft.usdt_wallet }}
</div>
{% endmacro %}

{% macro invoice_off_days(off_days) %}
{% if off_days %}
<div class="section-title">Off days this month:</div>
{% for off_day in off_days %}
<div class="off-day">{{ off_day | format_date }}</div>
{% endfor %}
{% endif %}
{% endmacro %}

{% macro invoice_vacation(draft, live_vacation=false) %}
<div class="section-title">Vacations (and Off days):</div>
<div class="vacation-block">
  <p class="vacation-line">Total used this year:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    {% if live_vacation %}<span id="vacation-used">{{ draft.vacation_used }}</span>{% else %}{{ draft.vacation_used }}{% endif %}
    days</p>
  <p class="vacation-line">Carried over last year(s):&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{{ draft.vacation_carried_over }} days</p>
  <p class="vacation-line">Remaining:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{{ draft.vacation_remaining }} days</p>
</div>
{% endmacro %}

{% macro invoice_footer() %}
<div class="invoice-footer" aria-hidden="true">
  <img class="footer-wave" src="static/invoice/image1.png" alt="">
  <img class="footer-wave" src="static/invoice/image2.png" alt="">
</div>
{% endmacro %}

{% macro invoice_body(draft, invoice_off_days=none) %}
{{ invoice_top(draft) }}
{{ invoice_off_days(invoice_off_days) }}
{{ invoice_vacation(draft) }}
{{ invoice_footer() }}
{% endmacro %}
```

Note: `live_vacation` param kept for API compatibility even though PDF path passes `false`.

- [ ] **Step 2: Run HTML fidelity tests**

```bash
pytest tests/test_pdf_renderer.py::test_pdf_html_uses_reference_assets \
  tests/test_pdf_renderer.py::test_pdf_html_has_four_column_items_table -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add app/templates/_invoice_body.html
git commit -m "feat: rebuild invoice PDF template for Google Doc reference layout"
```

---

### Task 5: Remove obsolete SVG and run full suite

**Files:**
- Delete: `static/invoice-signature.svg`
- Modify: `docs/superpowers/specs/2026-07-06-invoice-pdf-fidelity-design.md` (status → Approved)

- [ ] **Step 1: Delete unused signature SVG**

```bash
rm static/invoice-signature.svg
```

- [ ] **Step 2: Update spec status line**

In `docs/superpowers/specs/2026-07-06-invoice-pdf-fidelity-design.md`, change:

```markdown
**Status:** Pending user review
```

to:

```markdown
**Status:** Approved
```

- [ ] **Step 3: Run full test suite**

```bash
pytest -v
```

Expected: all tests PASS

- [ ] **Step 4: Smoke-generate a PDF**

```bash
python -c "
from datetime import date
from app.models import InvoiceDraft, PartyInfo
from app.pdf_renderer import render_invoice_pdf
draft = InvoiceDraft(
    invoice_number=2334974,
    invoice_date=date(2026, 6, 30),
    amount_eur=1500,
    usdt_wallet='TCEvAY15PUDMrb5uu35F1EhG21u2RYHtoS',
    from_party=PartyInfo(name='Ramin Maazallahi', email='r.mazallahi-ext@initiative-crm.com', location='Mashad, Iran'),
    billed_to=PartyInfo(name='Boris Clement', company='Initiative solutions', location='Valreas, France'),
    off_days=[],
    vacation_used=6,
    vacation_carried_over=7,
    vacation_remaining=31,
    month_label='June 2026',
)
open('/tmp/invoice-test.pdf', 'wb').write(render_invoice_pdf(draft))
print('Wrote /tmp/invoice-test.pdf', len(render_invoice_pdf(draft)), 'bytes')
"
```

Expected: PDF file written, size > 5000 bytes.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove obsolete invoice signature SVG; approve PDF fidelity spec"
```

---

### Task 6: Visual compare pass (manual tune)

**Files:**
- Modify (if needed): `static/invoice-document.css`, `app/templates/_invoice_body.html`

- [ ] **Step 1: Side-by-side compare**

Open `/tmp/invoice-test.pdf` alongside the reference PDF screenshot. Check:
- Oswald 48pt title size
- Green header `#96EE71` and gold borders `#E9C119`
- Signature position over total row
- Footer waves flush at page bottom
- Vacation tab spacing
- 72pt page margins

- [ ] **Step 2: Tune CSS if gaps found**

Common tweaks:
- `.invoice-document` bottom padding (increase/decrease `200pt`)
- `.invoice-signature` `right` / `bottom` / `width`
- `.parties-table` column widths via `table-layout: fixed` and `%` widths

- [ ] **Step 3: Re-run tests and commit any tune**

```bash
pytest tests/test_pdf_renderer.py -v
git add static/invoice-document.css app/templates/_invoice_body.html
git commit -m "fix: tune PDF layout spacing to match reference export"
```

(Skip commit if no tune needed.)

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| Oswald/Nunito bundled locally | Task 1 |
| PNG signature + footer | Task 1, 4 |
| Colors `#96EE71`, `#E9C119` | Task 3 |
| 72pt padding, 4-col table | Task 3, 4 |
| Relative asset paths for WeasyPrint | Task 4 |
| Preview = download (same renderer) | No code change — verified Task 5 |
| `generate.html` unchanged | No task touches it |
| Automated fidelity tests | Task 2 |
| Remove SVG footer/signature | Task 5 |

## Success criteria (from spec)

1. App PDF matches Google Doc export at a glance — verify in Task 6
2. Preview PDF === downloaded PDF — same `render_invoice_pdf()` path
3. Settings/chrome unchanged — no files modified
4. Off-day editor still works — `generate.html` untouched
5. All tests pass — Task 5
