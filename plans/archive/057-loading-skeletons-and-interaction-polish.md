# Plan 057: Add loading skeletons and interaction polish

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
- **Depends on**: Plan 055 (typography) recommended but not required — the skeleton CSS
  and interactions don't depend on font changes, but testing after both plans land is ideal.
- **Category**: design / ux
- **Planned at**: commit `577ceb1`, 2026-07-14

## Why this matters

The landing page loads 5 remote JSON files (`hub_health.json`, `hub_bundle.json`,
`artifact_manifest.json`, `indicadores_hoy.json`, `comunas.json`) on page load. During
this time, the catalog grid, KPI strip, comunas table, and health dashboard show nothing
or a single small spinner. This creates a "broken page" impression for the 1–3 seconds
before data arrives. Modern data products use skeleton screens (animated placeholder shapes
matching the final layout) to signal "content is loading" instead of "content is missing."
Adding skeletons for the catalog (the first large section users see) and the KPI strip
(the first data-dependent element) dramatically improves perceived performance.

Additionally, three interaction polish items have high impact-to-effort ratios:
1. The catalog search has no "no results" state (just an empty grid) — add an empty state
2. Dataset card click targets are text-only; the entire card should be clickable (not just
   specific action buttons) to open the drawer, matching users' expectations
3. The drawer's close behavior should also respond to the Escape key (standard for modals)

## Current state

**Files involved:**
- `index.html` — CSS new rules + skeleton HTML placeholder blocks
- `app.js` — JavaScript to remove skeleton classes on data load, add empty state, card clicks, Escape key

**Current skeleton/spinner approach:**

```css
/* index.html:1639-1651 — the ONLY loading indicator */
.spinner {
    display: inline-block;
    width: 1.2rem;
    height: 1.2rem;
    border: 2px solid rgba(18, 61, 48, 0.1);
    border-radius: 50%;
    border-top-color: var(--accent-green);
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
```

**How app.js shows loading (app.js:776–780, catalog load):**

```javascript
// Current: just shows a spinner inside the catalog grid
catalogGrid.innerHTML = '<div class="spinner" style="margin: 2rem auto; display: block;" aria-label="Cargando catálogo"></div>';
```

**Current catalog search filter (app.js:480–493):**

```javascript
// Filters dataset cards by text match; hides non-matching cards with [hidden]
// No "no results" state — if no matches, the grid is just empty/blank
filteredCount = 0;
for (const card of catalogGrid.querySelectorAll("[data-dataset]")) {
    const matches = dataset.name.toLowerCase().includes(q)
        || dataset.description.toLowerCase().includes(q);
    card.hidden = !matches;
    if (matches) filteredCount++;
}
// NO code to show "no results" when filteredCount === 0
```

**Current dataset card interaction (app.js:680–730, catalog rendering):**

```javascript
// Cards have individual action buttons that open the drawer:
// <button class="dataset-action" onclick="showDatasetDrawer('dataset_name')">Ficha técnica</button>
// The card <div> itself is NOT clickable — only the buttons are.
```

**Current drawer close behavior (app.js:844–855):**

```javascript
// Close button click:
drawerClose.addEventListener("click", closeDrawer);
// Backdrop click:
drawerBackdrop.addEventListener("click", closeDrawer);
// NO Escape key handler
```

**Repo conventions for app.js:**
- Vanilla JavaScript, no framework
- DOM manipulation via `document.getElementById` and `querySelector`
- HTML generation via template literals (backtick strings with `${}` interpolation)
- Event handlers use `addEventListener`
- CSS classes toggled with `classList.add/remove/toggle`
- All animation uses CSS `@keyframes`, never JS-based animation

**Exemplar pattern — how drawer active state works (app.js:800–810):**

```javascript
function openDrawer(datasetName) {
    drawer.classList.add("active");
    drawerBackdrop.classList.add("active");
    document.body.style.overflow = "hidden";
}

function closeDrawer() {
    drawer.classList.remove("active");
    drawerBackdrop.classList.remove("active");
    document.body.style.overflow = "";
}
```

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Format check | `make format-check` | exit 0 |
| Lint | `make lint` | exit 0 |
| Smoke test | `make verify-landing` | exit 0 |
| Doctor check | `make doctor` | exit 0, sync_docs OK |

## Scope

**In scope:**
- `index.html` — add CSS for skeletons, no-results empty state, card click cursor
- `app.js` — add skeleton removal logic, no-results message, card click handler, Escape key handler

**Out of scope:**
- `playground.js` — DuckDB-Wasm has its own lazy-init pattern; not changed
- Skeleton screens for the comunas table or health dashboard (deferred — catalog is the
  highest-traffic section and the best return on skeleton effort; the spinner is acceptable
  for secondary sections)
- Any change to the data-fetching or caching strategy — this plan adds UI polish, not
  performance optimization
- Dark mode skeleton colors (deferred until dark mode is implemented)
- `privacy.html`

## Git workflow

- Branch: `advisor/057-loading-skeletons`
- Commit: conventional commits with `feat(landing):` prefix; 2 commits:
  1. "feat(landing): add skeleton loading states for catalog and KPIs"
  2. "feat(landing): add empty search state, card click, and Escape key to drawer"
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add CSS for skeleton screens

Add to `index.html`'s `<style>` block, after the existing `.spinner` rules (around line 1651):

```css
/* Skeleton loading placeholder */
.skeleton-pulse {
    background: linear-gradient(
        90deg,
        var(--border-color) 25%,
        #e8e6dc 37%,
        var(--border-color) 63%
    );
    background-size: 400% 100%;
    animation: skeleton-shimmer 1.4s ease infinite;
    border-radius: 4px;
}

@keyframes skeleton-shimmer {
    0% { background-position: 100% 50%; }
    100% { background-position: 0 50%; }
}

/* Skeleton card shape — matches .dataset-card dimensions */
.skeleton-card {
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    background: var(--panel-bg);
}

.skeleton-card .skeleton-title {
    height: 1.1rem;
    width: 55%;
}

.skeleton-card .skeleton-desc {
    height: 0.875rem;
    width: 90%;
}

.skeleton-card .skeleton-meta {
    height: 0.75rem;
    width: 40%;
}

/* Skeleton KPI — matches .kpi-card dimensions */
.skeleton-kpi {
    padding: 1.5rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    border-right: 1px solid var(--border-color);
    background: var(--panel-bg);
}

.skeleton-kpi .skeleton-label {
    height: 0.74rem;
    width: 60%;
}

.skeleton-kpi .skeleton-value {
    height: 1.45rem;
    width: 80%;
}

/* Empty state for no search results */
.no-results-message {
    padding: 3rem 1.5rem;
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.92rem;
    line-height: 1.5;
}

.no-results-message strong {
    color: var(--text-primary);
}

/* Card click affordance */
.dataset-card {
    cursor: pointer;       /* add to existing rule */
}
```

**Verify**: `grep -c "skeleton-pulse\|skeleton-shimmer\|skeleton-card\|skeleton-kpi\|no-results-message" index.html` returns ≥ 8.

### Step 2: Add skeleton HTML placeholders in the catalog and KPI sections

**Catalog skeleton** — replace the spinner in `app.js::loadCatalog()` with skeleton cards.
Find the line in `app.js` (around line 776–780):

```javascript
catalogGrid.innerHTML = '<div class="spinner" style="margin: 2rem auto; display: block;" aria-label="Cargando catálogo"></div>';
```

Replace with:

```javascript
catalogGrid.innerHTML = `
    <div class="catalog-grid-sub" aria-label="Cargando catálogo">
        <div class="skeleton-card"><div class="skeleton-pulse skeleton-title"></div><div class="skeleton-pulse skeleton-desc"></div><div class="skeleton-pulse skeleton-meta"></div></div>
        <div class="skeleton-card"><div class="skeleton-pulse skeleton-title"></div><div class="skeleton-pulse skeleton-desc"></div><div class="skeleton-pulse skeleton-meta"></div></div>
        <div class="skeleton-card"><div class="skeleton-pulse skeleton-title"></div><div class="skeleton-pulse skeleton-desc"></div><div class="skeleton-pulse skeleton-meta"></div></div>
        <div class="skeleton-card"><div class="skeleton-pulse skeleton-title"></div><div class="skeleton-pulse skeleton-desc"></div><div class="skeleton-pulse skeleton-meta"></div></div>
    </div>
`;
```

**KPI skeleton** — find the KPI container setup in `app.js::loadKPIs()`. If no explicit
skeleton exists, add one before the fetch. Look for the KPI rendering code (around line
950–1050 in app.js). The KPI cards are inside a `.kpi-container` div. Add the following
at the top of the `loadKPIs()` function, before the fetch:

```javascript
const kpiContainer = document.querySelector('.kpi-container');
if (kpiContainer) {
    kpiContainer.innerHTML = `
        <div class="skeleton-kpi"><div class="skeleton-pulse skeleton-label"></div><div class="skeleton-pulse skeleton-value"></div></div>
        <div class="skeleton-kpi"><div class="skeleton-pulse skeleton-label"></div><div class="skeleton-pulse skeleton-value"></div></div>
        <div class="skeleton-kpi"><div class="skeleton-pulse skeleton-label"></div><div class="skeleton-pulse skeleton-value"></div></div>
        <div class="skeleton-kpi"><div class="skeleton-pulse skeleton-label"></div><div class="skeleton-pulse skeleton-value"></div></div>
    `;
}
```

**Verify**: `grep -n "skeleton-card\|skeleton-kpi" app.js` returns the new lines.

### Step 3: Add "no results" empty state for catalog search

In `app.js`, find the catalog search filter logic (around line 480–493). After the for loop
that hides non-matching cards, add:

```javascript
// After the for loop that sets card.hidden:

// Remove any existing "no results" message
const existingNoResults = catalogGrid.querySelector('.no-results-message');
if (existingNoResults) existingNoResults.remove();

if (filteredCount === 0 && catalogGrid.querySelectorAll('[data-dataset]').length > 0) {
    const noResults = document.createElement('div');
    noResults.className = 'no-results-message';
    noResults.innerHTML = '<strong>Sin resultados</strong><br>Prueba con otro término de búsqueda.';
    catalogGrid.appendChild(noResults);
}
```

**Verify**: `grep -n "no-results-message\|Sin resultados" app.js` returns the new lines.

### Step 4: Make dataset cards fully clickable + add Escape key to drawer

**Card click handler** — in `app.js`, find the catalog rendering function `renderCatalog()`
(around line 680). After the cards are inserted into the DOM, add a delegated click handler:

```javascript
// Add after renderCatalog inserts cards into catalogGrid:

catalogGrid.addEventListener('click', (event) => {
    const card = event.target.closest('[data-dataset]');
    if (!card) return;
    // Don't trigger if the user clicked a specific action button, a copy button,
    // or a link — let those elements handle their own clicks
    if (event.target.closest('button, a, .dataset-example-tab, .dataset-example-copy')) return;
    const datasetName = card.getAttribute('data-dataset');
    if (datasetName && typeof showDatasetDrawer === 'function') {
        showDatasetDrawer(datasetName);
    }
});
```

**Escape key handler** — add to the existing event listener section of `app.js` (near line 844
where drawer event listeners are set up):

```javascript
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && drawer.classList.contains('active')) {
        closeDrawer();
    }
});
```

**Verify**:
- `grep -n "closest.*data-dataset" app.js` returns the card click handler
- `grep -n "key.*Escape\|Escape.*key" app.js` returns the Escape key handler

### Step 5: Verify all smoke tests pass

```bash
make verify-landing
```

```bash
make lint
make format-check
make doctor
```

**Expected**: All exit 0. The smoke tests don't assert on skeleton visibility or card-click
behavior, so they should pass without modification.

## Test plan

No new tests for visual-only changes. The functional changes (Escape key, card click) are
simple event listeners that the Playwright smoke tests implicitly exercise when interacting
with the catalog and drawer.

## Done criteria

- [ ] `grep -c "skeleton-pulse" index.html` returns ≥ 1
- [ ] `grep -c "skeleton-shimmer" index.html` returns ≥ 1
- [ ] `grep -c "skeleton-card\|skeleton-kpi" app.js` returns ≥ 2
- [ ] `grep -c "no-results-message" app.js` returns ≥ 1
- [ ] `grep -c "closest.*data-dataset" app.js` returns ≥ 1
- [ ] `grep -c "Escape" app.js` returns ≥ 1
- [ ] `grep -c "cursor: pointer" index.html` returns ≥ 1 (on `.dataset-card`)
- [ ] `make lint` exits 0
- [ ] `make format-check` exits 0
- [ ] `make doctor` exits 0
- [ ] `make verify-landing` exits 0
- [ ] No files outside `index.html` and `app.js` are modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- The code at the locations in "Current state" doesn't match the excerpts (codebase drifted).
- `make verify-landing` fails after changes (could indicate the skeleton HTML structure
  interferes with Playwright's element selectors).
- The skeleton shimmer animation causes CPU spikes or jank in Playwright — if so, reduce
  the animation complexity (remove the gradient and use a simpler pulse opacity animation).
- The `cursor: pointer` on `.dataset-card` causes a visual conflict with any existing
  cursor rules on child elements (buttons already have their own `cursor: pointer`).

## Maintenance notes

- The skeleton HTML is hardcoded in `app.js` as template literals. If the catalog card
  layout changes (Plan 048 already cleaned it up), update the skeleton to match.
- The `no-results-message` is appended to `catalogGrid`, not to a specific category
  sub-grid. If the catalog layout is restructured, the append target may need updating.
- The Escape key handler on `document` is intentionally global — it's removed when the
  drawer is closed (the `if` check). If more modals/dialogs are added in a future plan,
  this handler should be refactored into a `closeActiveModal()` abstraction.
- The skeleton shimmer uses `background-size: 400% 100%` with a gradient animation.
  If this causes rendering issues on low-end mobile devices, fall back to a simpler
  opacity pulse: `animation: skeleton-pulse 1.5s ease-in-out infinite` with
  `@keyframes skeleton-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }`.
