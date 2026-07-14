# Plan 056: Improve visual rhythm, spacing, and section hierarchy

> **Executor instructions**: Follow this plan step by step. Run every verification command
> and confirm the expected result before moving to the next step. If anything in the
> "STOP conditions" section occurs, stop and report — do not improvise. When done,
> update the status row for this plan in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 577ceb1..HEAD -- index.html app.js`
> If any of these files changed since this plan was written, compare the "Current state"
> excerpts against the live code before proceeding; on a mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: 055 (typography) — the spacing values use sizes that depend on the new
  font metrics; execute 055 first.
- **Category**: design / dx
- **Planned at**: commit `577ceb1`, 2026-07-14

## Why this matters

The landing page is a single 2,919-line HTML file with 14 distinct sections stacked
vertically. The current layout uses a flat `3rem` gap between all `<main>` children
and a consistent `2rem` padding on most panels. While clean, this creates visual
monotony — a user scrolling from Hero → KPIs → Status → Package → Catalog → Coverage
→ Trust → Quickstart → SQL Explorer → Comunas → Health → Manifesto → Contribute
→ Support → Footer experiences the same visual rhythm throughout, making it hard
to distinguish high-value sections (catalog, health) from secondary ones (support,
quickstart). Strategic spacing differentiation, a sticky navigation header, and
visual separators between content zones will guide attention, reduce scroll fatigue,
and make the page feel curated rather than auto-generated.

## Current state

**Files involved:**
- `index.html` — CSS in `<style>` block (lines 297–2467), HTML body (lines ~2470–2909)

**Current spacing values (flat, undifferentiated):**

```css
/* index.html:453-459 */
main {
    padding: 3.5rem 2rem;
    display: flex;
    flex-direction: column;
    gap: 3rem;          /* ← same gap between ALL sections */
    flex: 1;
}
```

**Section inventory (from top to bottom, HTML order):**

| # | Section | CSS class | Lines (approx) |
|---|---|---|---|
| 1 | Header + Logo | `header` | ~2470–2490 |
| 2 | Hero / Intro | `.intro` | ~2492–2550 |
| 3 | KPI Strip | `.kpi-container` | ~2552–2580 |
| 4 | Pipeline Status | `.status-banner` | ~2582–2620 |
| 5 | Package Download | `.package-section` | ~2622–2670 |
| 6 | Catalog | `.catalog-section` | ~2672–2750 |
| 7 | Coverage & Trust (Cobertura) | `.section-shell` | ~2752–2800 |
| 8 | Quickstart | `.quickstart-section` | ~2802–2840 |
| 9 | SQL Explorer | (playground) | ~2842–2870 |
| 10 | Comunas Explorer | `.table-container` | ~2872–2890 |
| 11 | Health Dashboard | (in-app generated) | ~2892+ |
| 12 | Manifesto | `.manifesto` | within main |
| 13 | Contribute | `.participate-section` | within main |
| 14 | Support | `.support-section` | within main |
| 15 | Footer | `footer` | ~2900+ |

**Existing responsive breakpoints:**

```css
/* index.html:1682 — 960px */
@media (max-width: 960px) { ... }

/* index.html:1742 — 580px */
@media (max-width: 580px) { ... }
```

**Header is NOT sticky** (scrolls away with content):

```css
/* index.html:398-404 */
header {
    padding: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
}
/* No position: sticky or top: 0 */
```

**Repo conventions:** CSS changes go in `index.html`'s `<style>` block. The builder
(`src/builders/landing.py`) only touches the JSON-LD block and version query param —
it does not generate or touch CSS.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Format check | `make format-check` | exit 0 |
| Lint | `make lint` | exit 0 |
| Smoke test | `make verify-landing` | exit 0 |
| Doctor check | `make doctor` | exit 0, sync_docs OK |

## Scope

**In scope** (the only file you should modify):
- `index.html` — CSS spacing adjustments + add sticky header CSS + minor HTML for sticky nav

**Out of scope** (do NOT touch):
- `app.js` — no spacing/layout logic lives here
- `playground.js` — no layout changes
- Any content changes (text, copy, section ordering) — this plan is spacing ONLY
- Adding a sidebar, collapsing sections, or tab-based navigation — those are information
  architecture decisions for a future plan; this plan is visual rhythm only
- The DuckDB playground's internal console layout (`.playground-console`, `.console-*`)

## Git workflow

- Branch: `advisor/056-visual-rhythm`
- Commit: conventional commits with `feat(landing):` prefix; split into 2 commits:
  1. "feat(landing): add sticky header with backdrop blur"
  2. "feat(landing): differentiate section spacing and add visual separators"
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add sticky header with backdrop blur

The current header scrolls away with the page. Make it sticky so the logo, nav links
(GitHub, Docs, API Reference), and version badge stay visible.

In `index.html`, add to the `header` CSS rule (around line 398):

```css
header {
    padding: 1.25rem 2rem;    /* reduced from 2rem — sticky headers should be compact */
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(247, 246, 240, 0.85);  /* var(--bg-color) with transparency */
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);    /* Safari support */
    border-bottom: 1px solid var(--border-color);
    /* keep existing: display, justify-content, align-items, max-width, margin, width */
}
```

**Note**: The `padding` reduction compensates for the now-always-visible header.
The `background` transparency + `backdrop-filter` creates a frosted-glass effect
that's modern and widely supported (Safari 9+, Chrome 76+, Firefox 103+).

**Also add**: a spacer to prevent the sticky header from covering anchor targets
when the page scrolls to `#dataset-*` hash links:

```css
/* Add this new rule */
html {
    scroll-padding-top: 72px;  /* header height ≈ 3.5rem at 16px base */
    scroll-behavior: smooth;
}
```

**Verify**: `grep -n "position: sticky" index.html` returns the header rule.
`grep -n "scroll-padding-top" index.html` returns the html rule.

### Step 2: Differentiate section spacing

Replace the flat `gap: 3rem` on `<main>` with CSS custom properties that create
three spacing tiers:

```css
/* Add to :root (after existing --font-* variables, around line 326): */
--space-section-tight: 2rem;
--space-section-normal: 3.5rem;
--space-section-loose: 5rem;

/* Replace "gap: 3rem" on main (line 457): */
main {
    /* ... keep existing properties ... */
    gap: var(--space-section-normal);
}
```

Then add contextual spacing overrides for specific sections:

```css
/* Hero → next section: tighter connection */
.intro + .kpi-container {
    margin-top: calc(var(--space-section-normal) - var(--space-section-tight));
}

/* After catalog → coverage/trust: larger separator for visual break */
.catalog-section + .section-shell {
    margin-top: calc(var(--space-section-loose) - var(--space-section-normal));
}

/* Manifesto → next section: more breathing room after a dark block */
.manifesto + * {
    margin-top: calc(var(--space-section-loose) - var(--space-section-normal));
}

/* Last sections before footer: tighter */
.participate-section + .support-section {
    margin-top: calc(var(--space-section-tight) - var(--space-section-normal));
}
```

**Verify**: `grep -c "space-section" index.html` returns ≥ 8 (3 definitions + 4 overrides + main's gap reference).

### Step 3: Add subtle horizontal rules between major zones

Add a visual separator using `::before` pseudo-element between the Catalog and Coverage sections
(where the page transitions from "data catalog" to "trust & methodology"):

```css
.section-shell::before {
    content: '';
    display: block;
    width: 60px;
    height: 3px;
    background: var(--accent-green);
    border-radius: 2px;
    margin-bottom: 1.5rem;
    opacity: 0.25;
}
```

And for the Manifesto (dark green block), add a similar separator above to signal
a tonal shift:

```css
.manifesto::before {
    content: '';
    display: block;
    width: 60px;
    height: 3px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
    margin-bottom: 1.5rem;
}
```

**Verify**: `grep -n "section-shell::before\|manifesto::before" index.html` returns both rules.

### Step 4: Verify across breakpoints

The new spacing values use `rem` units which scale with the base font size, so they work
at all breakpoints. Run the smoke tests:

```bash
make verify-landing
```

**Expected**: exit 0. The smoke tests confirm the page renders and interactive elements
work. The sticky header doesn't break any existing test assertions.

Also verify the responsive breakpoints still apply correctly:

```bash
make lint
make format-check
make doctor
```

**Expected**: All three exit 0.

### Step 5: Verify no scroll jank with sticky header

The sticky header must not cause layout shift (CLS). Since the header was already in
the normal document flow before becoming sticky, its removal from flow on scroll should
not cause content to jump — but the reduced padding (`2rem` → `1.25rem`) might. To compensate:

```css
/* The reduced header padding needs to be balanced by the main content not jumping up.
   Since the header goes sticky at scroll, it already occupies space via normal flow.
   The only concern is the height difference: 2rem×2=4rem → 1.25rem×2=2.5rem.
   Add a small top padding to main to compensate the visual density: */
main {
    padding: 3.5rem 2rem 4rem;  /* keep 3.5rem top, add 0.5rem to bottom */
}
```

## Test plan

No new tests. The visual changes are layout-only; `make verify-landing` provides the
functional safety net. If the operator wants visual regression testing, they can use
Playwright screenshots, but that is out of scope for this plan.

## Done criteria

- [ ] `grep -n "position: sticky" index.html` returns exactly 1 match (the header rule)
- [ ] `grep -n "backdrop-filter" index.html` returns ≥ 1 match
- [ ] `grep -n "scroll-padding-top" index.html` returns 1 match
- [ ] `grep -c "space-section" index.html` returns ≥ 8
- [ ] `grep -c "section-shell::before\|manifesto::before" index.html` returns ≥ 2
- [ ] `make lint` exits 0
- [ ] `make format-check` exits 0
- [ ] `make doctor` exits 0
- [ ] `make verify-landing` exits 0
- [ ] No files outside `index.html` are modified (`git status --short`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- The `header` CSS rule or `main` CSS rule in `index.html` doesn't match the "Current state"
  excerpts (code has drifted).
- `make verify-landing` fails after the sticky header change (possible if the smoke test's
  Playwright viewport calculations change).
- The sticky header causes content to be inaccessible behind the header — test by scrolling
  to a hash-anchored section (`#catalog-section` or a `#dataset-*` link).
- You discover the header height is significantly different from 72px (the `scroll-padding-top`
  value) at any breakpoint.

## Maintenance notes

- The `scroll-padding-top: 72px` value is coupled to the header height. If the header's
  padding, font size, or content changes, this value must be updated. A future plan could
  compute it dynamically with a `--header-height` CSS variable if header changes are frequent.
- The `backdrop-filter` property requires `-webkit-` prefix for Safari ≤ 17. This is included.
- If a future plan adds a search bar to the header, the sticky behavior enables it to be
  always accessible — this plan intentionally makes the header sticky to unlock that future use.
- The spacing tier values (2rem / 3.5rem / 5rem) follow a 1:1.75:2.5 ratio, not a strict
  modular scale. If the design system is formalized later, these should be aligned.
