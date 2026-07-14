# Plan 055: Overhaul typography for professional data readability

> **Executor instructions**: Follow this plan step by step. Run every verification command
> and confirm the expected result before moving to the next step. If anything in the
> "STOP conditions" section occurs, stop and report — do not improvise. When done,
> update the status row for this plan in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 577ceb1..HEAD -- index.html app.js playground.js privacy.html`
> If any of these files changed since this plan was written, compare the "Current state"
> excerpts against the live code before proceeding; on a mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx / design
- **Planned at**: commit `577ceb1`, 2026-07-14

## Why this matters

The current font stack — Lora (display) + IBM Plex Sans (body) + IBM Plex Mono (code) — is distinctive
but optimized for editorial/book reading, not data-dense interfaces. IBM Plex Sans has a narrow,
semi-condensed character that reduces legibility at small sizes (0.72rem–0.88rem) where most dataset
metadata, labels, and table content live. Lora's serif character creates a "literary" feel that
undermines the data product's technical credibility. Swapping to a clean, modern, high-legibility
stack designed for data products raises perceived value, improves readability of dense catalog cards
and tables, and signals "production-grade data infrastructure" instead of "personal wiki."

The font swap is the single highest-leverage visual change per line of CSS touched (14 lines in the
`:root`, 2 lines in Google Fonts links). Font rendering is loaded via CDN — the new stack uses a
battle-tested variable font family with excellent hinting, broader language support, and better
performance than three separate IBM Plex files.

## Current state

**Files involved:**

- `index.html` — embedded `<style>` block (lines 297–2467), Google Fonts `<link>`s (lines ~7–14)
- `app.js` — dynamic HTML that references `--font-mono`/`--font-sans`/`--font-display` indirectly via CSS
- `playground.js` — uses `var(--font-mono)` via CSS (`.playground-console`)

**Relevant CSS custom properties in index.html (lines 321–323):**

```css
--font-display: 'Lora', Georgia, serif;
--font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
```

**Google Fonts links currently loaded (lines ~7–14):**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&display=swap" rel="stylesheet">
```

**Where `--font-display` is used (Lora → headings/display):**
- `.intro h2` (line 478)
- `.status-title, .package-title, .catalog-title, .quickstart-title` (line 625)
- `.section-heading h2` (line 1136)
- `.manifesto h2` (line 1380)
- `.explorer-heading h2` (line 1411)
- `.participate-section h2` (line 1313)
- `.support-section h2` (line 1346)
- `.catalog-category-title` (line 2139)
- `.dataset-name` (line 2210)
- `.drawer-dataset-name` (line 2028)

**Repo convention:** All CSS is inline in `index.html`'s `<style>` block. No external stylesheets for
the landing page. Changes to CSS go directly in `index.html`. The `src/builders/landing.py` builder only
patches the JSON-LD block and version URL — it does not regenerate CSS.

**Exemplar for matching conventions:** See Plan 047 (archived) which replaced `font-family: 'Fira Code'`
with `var(--font-mono)` — a single-property replacement in `index.html` with `make verify-landing` verification.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Format check | `make format-check` | exit 0 |
| Lint | `make lint` | exit 0 |
| Smoke test | `make verify-landing` | exit 0, no errors |
| Doctor check | `make doctor` | exit 0, sync_docs OK |

## Scope

**In scope** (the only files you should modify):
- `index.html` — replace Google Fonts `<link>` tags + update 3 `--font-*` custom properties

**Out of scope** (do NOT touch, even though they look related):
- `app.js` — uses CSS variables only; no font-family hardcoded (verified by grep)
- `playground.js` — inherits `--font-mono` from CSS
- `privacy.html` — has its own `font-family` declaration; updated separately in Plan 046
- `docs/stylesheets/extra.css` — MkDocs theme, not landing page
- Any change to font sizes, weights, or letter-spacing — only the font FAMILY changes
- Any change to Google Fonts URL loading strategy (stays as `<link>` for now; `@import` optimization is deferred)
- Any addition of new font weights not currently in use

## Git workflow

- Branch: `advisor/055-typography-overhaul`
- Commit: single commit with `feat(landing):` prefix
- Do NOT push or open a PR unless the operator instructed it.

## Suggested executor toolkit

- Use the `ui-ux-pro-max` skill for typography guidance: run
  `python3 skills/ui-ux-pro-max/scripts/search.py "Source Serif professional data" --domain google-fonts`
  if you need to verify the font recommendation.

## Steps

### Step 1: Replace the font-family CSS custom properties

In `index.html`, replace the three `--font-*` custom properties in the `:root` block with this stack:

**Current** (line 321–323):

```css
--font-display: 'Lora', Georgia, serif;
--font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
```

**New:**

```css
--font-display: 'Source Serif 4', Georgia, 'Times New Roman', serif;
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
--font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, 'Cascadia Code', 'Fira Code', Menlo, Monaco, monospace;
```

**Verify**: `grep -n "font-display:\|font-sans:\|font-mono:" index.html` shows the new values.

**Design rationale** (for reviewer, not for code comments):
- **Source Serif 4** replaces Lora: a workhorse serif by Adobe designed for extended UI reading;
  still carries authority/heritage (important for a government data product) but with better
  screen rendering, more weights (12 variable axes vs. Lora's 4), and a more neutral tone.
- **Inter** replaces IBM Plex Sans: the most battle-tested UI sans-serif for data-dense
  interfaces; designed specifically for screen legibility at 11px+, with a tall x-height that
  the narrow IBM Plex Sans lacks. Used by GitHub, Figma, Stripe, Vercel.
- **JetBrains Mono** replaces IBM Plex Mono: designed for code but with ligatures that IBM
  Plex lacks; better differentiation between similar glyphs (l/1, 0/O); the coding-specific
  character fits a data product better than IBM Plex Mono's typewriter-courier feel.

### Step 2: Replace the Google Fonts `<link>` tags

In `index.html`, replace the Google Fonts preconnect and stylesheet links with the new font
stack. Locate the 3 existing `<link>` tags and replace them:

**Current** (the 3 consecutive Google Fonts `<link>` tags):

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&display=swap" rel="stylesheet">
```

**New** — match the existing weight/italic usage exactly:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400;1,14..32,600&family=JetBrains+Mono:ital,wght@0,400;0,600;1,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,500;0,8..60,600;0,8..60,700;1,8..60,400;1,8..60,600&display=swap" rel="stylesheet">
```

**Weight mapping** (existing → new, to verify no weight is missed):
| Current | Weights loaded | New | Weights loaded |
|---|---|---|---|
| Lora | 400, 500, 600, 700 + italic 400, 600 | Source Serif 4 | 400, 500, 600, 700 + italic 400, 600 |
| IBM Plex Sans | 400, 500, 600, 700 + italic 400, 600 | Inter | 400, 500, 600, 700 + italic 400, 600 |
| IBM Plex Mono | 400, 600 + italic 400 | JetBrains Mono | 400, 600 + italic 400 |

**Verify**: `grep "fonts.googleapis.com" index.html` shows the new Inter + Source Serif 4 + JetBrains Mono URL and returns no IBM Plex or Lora references.

### Step 3: Verify visual consistency

Run the smoke tests:

```bash
make verify-landing
```

**Expected**: exit 0, no errors. The landing page smoke tests confirm the page loads, the catalog
renders, the comunas table populates, and the SQL explorer works. No font-family assertions exist
in the smoke tests, so they should pass without modification.

**Additional manual verification**: Run `make build && make verify` to regenerate the landing page
locally (this will sync the version number in `app.js`). Then open `index.html` in a browser or
use Playwright to take a screenshot and visually verify:
1. Headings render in Source Serif 4 (serif)
2. Body text renders in Inter (sans-serif)
3. Code blocks, monospace badges, and KPI values render in JetBrains Mono
4. The `font-display: swap` ensures text is visible during font load (FOIT prevention)

### Step 4: Verify no regressions in CI gates

```bash
make lint
make format-check
make doctor
```

**Expected**: All three exit 0.

## Test plan

No new tests are needed — font family changes are visual-only and CSS properties are not
asserted by any existing test. The smoke tests in `scripts/verify_landing.py` cover the
functional surface (page loads, catalog renders, tables populate) which is unchanged.

Verification is visual: `make verify-landing` confirms the page still renders without errors.

## Done criteria

- [ ] `grep -n "font-display:\|font-sans:\|font-mono:" index.html` shows Source Serif 4 / Inter / JetBrains Mono
- [ ] `grep "fonts.googleapis.com" index.html` shows the new URL and returns no IBM Plex or Lora
- [ ] `grep -c "IBM Plex\|Lora" index.html` returns 0 (no stale references)
- [ ] `make lint` exits 0
- [ ] `make format-check` exits 0
- [ ] `make doctor` exits 0 (sync_docs OK)
- [ ] `make verify-landing` exits 0
- [ ] No files outside `index.html` are modified (`git status --short` shows only `index.html`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- The Google Fonts `<link>` at the expected position doesn't match the "Current" excerpt above
  (the codebase has drifted since this plan was written).
- A step's verification fails twice after a reasonable fix attempt.
- The fix appears to require touching `app.js`, `playground.js`, `privacy.html`, or any other
  file beyond `index.html`.
- `make verify-landing` fails after the font change (unlikely, but stop and investigate if
  it does — could indicate a Playwright rendering issue with the new fonts).
- You discover that any element has `font-family` hardcoded in `index.html` (not using the
  `--font-*` variables) that would miss the swap.

## Maintenance notes

- If custom font files are ever self-hosted (deferred from this plan), the `--font-*` variables
  would need `@font-face` declarations but the variable names stay the same.
- The `opsz` (optical size) axis on Inter and Source Serif 4 is specified in the Google Fonts
  URL — if font rendering at small sizes looks off, removing `opsz` from the URL makes both fonts
  use their default optical size.
- If a future plan adds a dark mode, verify the new fonts render legibly on both `#f7f6f0`
  (cream) and dark backgrounds — Inter and JetBrains Mono are designed for both; Source Serif 4
  may need a slightly higher weight (500→600) on dark backgrounds.
- The deferred font loading optimization (`@import` with `font-display: swap` in a `<style>`
  before `</head>`, or self-hosting with subsetting) would be a follow-up plan. This plan
  intentionally keeps the existing `<link>` loading pattern to minimize risk.
