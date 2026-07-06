# UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split invoice document (Google Doc fidelity) from app chrome (Uiverse neobrutalist) with strict CSS boundaries and PDF parity.

**Architecture:** Rewrite `invoice-document.css` + templates for plain Arial white-page layout. Rewrite `styles.css` with chrome tokens scoped outside `.invoice-document`. PDF uses document CSS only; web Generate wraps document in `.paper-card`.

**Tech Stack:** Jinja2, static CSS, WeasyPrint, pytest

**Spec:** `docs/superpowers/specs/2026-07-06-invoice-creator-ui-redesign.md`

---

### Task 1: Invoice document CSS + PDF template

**Files:**
- Modify: `static/invoice-document.css`
- Modify: `app/templates/invoice_pdf.html`

- [ ] White background, Arial 11pt, table-based parties/vacation, no Google Fonts
- [ ] PDF template uses tables matching Google Doc structure

### Task 2: Generate template structure

**Files:**
- Modify: `app/templates/generate.html`

- [ ] Separate `.paper-card` wrapper from `.invoice-document`
- [ ] Off-day editor in `.invoice-editor` chrome zone

### Task 3: Neobrutalist chrome CSS + templates

**Files:**
- Modify: `static/styles.css`
- Modify: `app/templates/settings.html`
- Modify: `app/templates/base.html`

- [ ] Chrome tokens, Uiverse-style inputs/buttons/cards
- [ ] Remove Cormorant from base; Source Sans 3 for chrome only

### Task 4: Tests + verification

**Files:**
- Modify: `app/pdf_renderer.py`
- Modify: `tests/test_pdf_renderer.py`

- [ ] `render_invoice_html()` helper
- [ ] Assert PDF HTML has no chrome classes; CSS has no Cormorant/CDN

### Task 5: Commit

```bash
git add static/ app/templates/ app/pdf_renderer.py tests/ docs/superpowers/plans/
git commit -m "feat: redesign UI with Google Doc invoice and neobrutalist chrome"
```
