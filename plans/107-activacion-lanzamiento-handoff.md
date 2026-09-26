# Plan 107: Handoff autocontenido — activación de lanzamiento (agente autónomo)

> **Para un agente pequeño (Cowork) ejecutando solo, sin contexto previo.**
> Este documento es autosuficiente: incluye qué es el proyecto, dónde vive,
> qué URLs usa, qué archivos toca, cómo verificar cada paso, qué hacer si algo
> falla (fallback) y cuándo detenerse (STOP). No asumas conocimiento externo.
>
> **Drift check (ejecutar primero)**:
> ```bash
> git rev-parse --short HEAD          # esperado: 056baf7 o un descendiente en main
> git status --short                  # esperado: vacío
> git branch --show-current           # esperado: main
> ```
> Si el árbol está sucio o `main` no está en `056baf7` o posterior, **STOP** y
> reporta (el repo cambió; este handoff puede estar desactualizado).

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW (docs + meta tag; no toca datos, extractores ni workflows)
- **Category**: distribution / handoff
- **Planned at**: commit `056baf7`, 2026-09-26
- **Ejecuta**: un agente pequeño con acceso al repo local y `gh` autenticado

---

## 0. Contexto mínimo del proyecto (leer antes de tocar nada)

**chile-hub** es una capa de datos pública y reproducible sobre datos oficiales
de Chile: 22 capas construibles (21 publicables) en Parquet/JSON/DuckDB/Excel,
consumibles con `pip install chile-hub`. El pipeline (extracción → build →
validación → publicación) corre en GitHub Actions y **aborta antes de publicar
datos malos**. El proyecto tiene una regla de oro: *si una validación falla, el
pipeline falla ruidosamente*.

| Dato | Valor |
|:---|:---|
| Repositorio | https://github.com/cortega26/chile-hub |
| Sitio (GitHub Pages) | https://tooltician.com/chile-hub/ |
| Paquete PyPI | https://pypi.org/project/chile-hub/ |
| Versión actual (`pyproject.toml`) | `1.37.7` |
| Commit de referencia | `056baf7` (2026-09-26) |
| Idioma | Español (código, docs y commits) |
| Licencia del código | MIT |

### Estructura del repo (solo lo que este plan necesita)

```
chile-hub/
├── index.html          # landing pública (se sirve como https://tooltician.com/chile-hub/)
├── Makefile            # targets: doctor, verify-landing, docs-build, test, sync-docs…
├── pyproject.toml      # versión del paquete + config de tooling
├── data/normalized/    # artefactos publicados (NO editar a mano)
│   ├── adoption.json               # métricas PyPI + descargas GitHub Releases (se refresca solo)
│   └── ...
├── docs/
│   ├── adoption-review.md          # doc de decisión con baseline y umbrales
│   ├── launch-pack.md              # material de difusión + leads de LinkedIn
│   └── ...
├── plans/              # planes de trabajo (este archivo es el 107)
├── scripts/            # verify_landing.py, sync_docs.py, etc.
├── tests/              # suite pytest
└── .venv/              # entorno Python (si no existe: `make bootstrap`, pesado)
```

### Cómo se opera el repo (comandos canónicos)

```bash
PY=.venv/bin/python          # el venv del proyecto
$PY -m pytest tests/ -q      # suite completa (~1 min)
make doctor                  # gates de integridad (exit 0 = verde)
make verify-landing          # smoke test Playwright de la landing
make docs-build              # construye docs mkdocs en reference/ (gitignored)
```

**Reglas del repo que NO se rompen:**
- No editar nada dentro de `data/normalized/` a mano (son artefactos generados).
- No correr extractores ni `make build` (pesado, usa red y ensucia el árbol).
- No tocar workflows, extractores, validaciones ni contratos.

### Flujo de git de este plan

1. Trabajar en el branch `advisor/107-activacion-lanzamiento`.
2. Commits convencionales en español (`docs(...)`, `feat(...)`).
3. **No push, no merge, no PR.** El operador revisa y pushea.
4. Los hooks de pre-commit corren al commitear (ruff, mypy, etc.). Si un hook
   **reformatea** archivos, el commit se aborta: hay que re-agregar y commitear
   de nuevo. Es normal, no es un error:
   ```bash
   git add -A && git commit -m "<mismo mensaje>"
   ```

---

## 1. Objetivo y alcance

**Objetivo:** dejar lista la activación de lanzamiento que no requiere cuentas
externas: (a) verificación de Google Search Console por meta tag/archivo,
(b) verificación del sitemap en vivo, (c) verificación de los issues de leads,
(d) verificación del primer schedule diario tras las reparaciones, (e) registro
del baseline de adopción.

**In scope** (únicos archivos que puedes modificar):
- `index.html` (solo si el operador entregó el token de GSC)
- `google<token>.html` en la raíz (solo método archivo, si aplica)
- `docs/adoption-review.md` (append de una entrada fechada)
- `docs/launch-pack.md` (estado verificado de respuestas; opcional)

**Out of scope (prohibido):**
- Publicar en LinkedIn, HN, dev.to; tocar Google, Cloudflare, Zenodo.
- Workflows, extractores, `src/`, `data/`, `contracts/`, tests.
- Crear issues (ya existen #107/#108/#109) o modificar los existentes.
- `make build`, `make extract`, `git push`, `git merge`.

---

## 2. Mapa de recursos y URLs (todo lo que este plan referencia)

| Recurso | URL / ruta | Para qué |
|:---|:---|:---|
| Landing | https://tooltician.com/chile-hub/ | Página que Google debe verificar |
| Sitemap índice | https://tooltician.com/chile-hub/sitemap.xml | Declara los 3 hijos |
| Sitemap páginas | https://tooltician.com/chile-hub/sitemap-pages.xml | Landing + privacy |
| Sitemap docs | https://tooltician.com/chile-hub/reference/sitemap.xml | 86 páginas mkdocs |
| Sitemap comunas | https://tooltician.com/chile-hub/comunas/sitemap.xml | 347 páginas |
| Search Console | https://search.google.com/search-console | UI del operador |
| Issues de leads | https://github.com/cortega26/chile-hub/issues/107 · /108 · /109 | Pedidos de datasets |
| Post LinkedIn | https://lnkd.in/p/d6Z7YBtW | Origen de los leads |
| Métricas PyPI/Releases | `data/normalized/adoption.json` | Se refresca cada lunes en CI |
| Métricas HF | https://huggingface.co/api/datasets/cortega26/chile-hub | Descargas/likes del mirror |
| Métricas GitHub | `gh api repos/cortega26/chile-hub` | Stars/forks |
| Baseline de adopción | `docs/adoption-review.md` (§ Baseline y § Registro) | Dónde se registra |
| Material de difusión | `docs/launch-pack.md` | Contexto de leads/estado |

**Cómo se sirve el sitio:** `tooltician.com/chile-hub/` es GitHub Pages sirviendo
la raíz de este repo. Por eso un archivo `google<token>.html` en la raíz queda
público en `https://tooltician.com/chile-hub/google<token>.html` **después de
que el operador pushee** (el deploy tarda ~1–2 min).

---

## 3. Prerrequisitos (verificar antes de empezar)

```bash
# 1) Repo y venv
git rev-parse --show-toplevel                 # raíz del repo (debes estar ahí)
test -x .venv/bin/python && echo "venv ok"    # si falta: STOP (no correr make bootstrap sin avisar)

# 2) GitHub CLI autenticado (para Steps 3 y 4)
gh auth status                                 # esperado: Logged in to github.com

# 3) Red (para Steps 2, 4 y 5)
curl -s -o /dev/null -w "%{http_code}\n" https://tooltician.com/chile-hub/   # esperado: 200
```

Si `gh` no está autenticado o no hay red: los steps que dependan de eso se
marcan `sin dato` y se reportan; el resto continúa.

---

## 4. Reglas de seguridad (obligatorias)

1. **No push ni merge.** Todo queda en el branch local.
2. **No inventar valores ni tokens.** Si falta un dato → `sin dato` + reporte.
3. **No tocar cuentas externas** (LinkedIn, GSC UI, Cloudflare, Zenodo).
4. **Un fallo repetido dos veces = STOP** y reporte; no parchear a ciegas.
5. **No ejecutar comandos destructivos** (`git reset --hard`, `git clean -f`,
   `rm -rf`) ni instalar dependencias globales.

---

## 5. Steps

### Step 0 — Baseline (siempre)

```bash
git checkout -b advisor/107-activacion-lanzamiento
.venv/bin/python -m pytest tests/test_ci_config.py -q -k "HttpAccess or Citation"
```
**Esperado**: branch creado; tests verdes. Si fallan sin haber tocado nada,
**STOP** (baseline roto, no es tu culpa).

---

### Step 1 — Google Search Console: meta tag de verificación

**Prerrequisito:** el operador entrega el token de verificación de Google
(string tipo `abc123...`). El operador lo obtiene en GSC → *Añadir propiedad* →
*Prefijo de URL* `https://tooltician.com/chile-hub/` → método *Etiqueta HTML*.

**Si NO hay token:** registra `Step 1: saltado (sin token)` en el reporte y
**pasa al Step 2**. No inventes un token ni uses un ejemplo.

**Procedimiento (método meta tag):**
1. Abre `index.html` y ubica la línea **8**:
   ```html
   <meta name="robots" content="index, follow">
   ```
   (está en el `<head>`, tras `<meta name="description" ...>`).
2. Inserta **inmediatamente después** (misma indentación de 4 espacios):
   ```html
   <meta name="google-site-verification" content="TOKEN_EXACTO_DEL_OPERADOR" />
   ```
3. **Verify**:
   ```bash
   grep -c 'name="google-site-verification"' index.html     # → 1
   make verify-landing                                       # → "Landing verification passed"
   make doctor                                               # → exit 0
   ```
4. Commit:
   ```bash
   git add index.html && git commit -m "feat(seo): verificación de Google Search Console (meta tag)"
   ```

**Fallback A — método archivo HTML:** si el operador entrega un archivo
(`google<hash>.html` con contenido exacto), créalo en la **raíz del repo** con
ese contenido exacto, verifica `test -f google*.html`, corre `make doctor` y
commitea `feat(seo): verificación de Google Search Console (archivo)`.
La verificación en vivo la hará el operador tras el push:
`https://tooltician.com/chile-hub/google<hash>.html`.

**Fallback B — método DNS TXT:** es una acción en Cloudflare del operador; no
hay nada que hacer en el repo. Regístralo en el reporte y sigue.

**STOP si:** el token no está y el operador pidió esperarlo (no continúes ese
step); o `make doctor` falla por algo que tocaste (revertir el cambio).

---

### Step 2 — Verificar el sitemap en vivo (pre-submit del operador)

```bash
curl -s https://tooltician.com/chile-hub/sitemap.xml | head -5
for u in sitemap-pages.xml reference/sitemap.xml comunas/sitemap.xml; do
  printf "%s -> " "$u"
  curl -s -o /dev/null -w "%{http_code}\n" "https://tooltician.com/chile-hub/$u"
done
```
**Esperado**: el índice empieza con `<sitemapindex`; los 3 hijos responden `200`.

**Fallback:** si un hijo da `404`, espera 5 minutos (el deploy de Pages puede
estar en curso) y repite **una vez**. Si persiste, anótalo en el reporte; **no
toques nada**.

**No hay commit en este step** (es solo verificación).

---

### Step 3 — Verificar los issues de leads

Contexto: los leads vienen del post de LinkedIn del 2026-09-26 y ya tienen
issue creado con el template `dataset_request`.

```bash
for n in 107 108 109; do
  gh issue view "$n" --json number,title,labels,state \
    --jq '"#\(.number) [\(.state)] \(.title) — labels: \([.labels[].name]|join(","))"'
done
```
**Esperado** (3 líneas, todas `OPEN` con labels `enhancement,dataset`):
```
#107 [OPEN] dataset: capa hidrometeorológica DGA (caudales/meteo) + DMC — labels: enhancement,dataset
#108 [OPEN] dataset: energía renovable y consumo eléctrico (fuente vigente CNE) — labels: enhancement,dataset
#109 [OPEN] dataset: datos de desastres naturales 2024-2026 (fuente por definir) — labels: enhancement,dataset
```

**Fallback:** si `gh` no está autenticado → registra `sin acceso a gh` y sigue.
Si un issue no existe, **STOP** y reporta (no lo crees: puede haber drift).

**No hay commit en este step.**

---

### Step 4 — Verificar el primer schedule diario tras las reparaciones

Contexto: el pipeline diario (cron 10:00 UTC) estuvo roto meses por dos causas
ya corregidas (pip-audit + fallback de `permisos_edificacion`). Este step
confirma que el schedule volvió a publicar solo.

```bash
gh run list --workflow pipeline-check.yml --event schedule --limit 3 \
  --json conclusion,createdAt,url \
  --jq '.[] | "\(.createdAt[:16]) \(.conclusion) \(.url)"'
```
**Esperado**: el run más reciente (creado ~10:00 UTC del día en curso) en
`success`. Si el más reciente es de ayer, espera unos minutos y repite **una vez**.

Si es `success`, confirma que publicó:
```bash
RUN=$(gh run list --workflow pipeline-check.yml --event schedule --limit 1 \
      --json databaseId --jq '.[0].databaseId')
gh run view "$RUN" --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
```
**Esperado** entre las líneas: `Publish verified data: success`.

**Fallback si falla:** captura el error real y **STOP**:
```bash
gh run view "$RUN" --log-failed 2>/dev/null | grep -E "##\[error\]|Traceback" | tail -20
```
No arregles código sin un plan nuevo; solo reporta.

---

### Step 5 — Registro de adopción (append en `docs/adoption-review.md`)

Contexto: `docs/adoption-review.md` tiene las secciones **Baseline**,
**Cómo leer las métricas**, **Umbrales de decisión** y **Registro**. Debes
agregar una entrada fechada al final de **Registro**.

**5.1 Recolectar métricas reales** (no estimar nunca):

```bash
# PyPI + GitHub Releases (archivo versionado, se refresca cada lunes)
cat data/normalized/adoption.json

# Hugging Face (descargas/likes del mirror)
curl -s https://huggingface.co/api/datasets/cortega26/chile-hub \
  | .venv/bin/python -c "import json,sys; d=json.load(sys.stdin); print(d.get('downloads'), d.get('likes'))"

# GitHub (stars/forks)
gh api repos/cortega26/chile-hub --jq '"stars=\(.stargazers_count) forks=\(.forks_count)"'
```

**5.2 Append** al final de la sección `## Registro` de `docs/adoption-review.md`:

```markdown
### AAAA-MM-DD — revisión (agente)

- PyPI (mes/semana/día): <X / Y / Z> — fuente: `data/normalized/adoption.json`
- HF: descargas <X>, likes <Y> — fuente: API HF
- GitHub: stars <X>, forks <Y> — fuente: API GitHub
- Search Console: `sin dato` (pendiente operador)
- Issues de leads: #107, #108, #109 — abiertos y etiquetados
- Schedule diario: <success | falló: primer error>
- Notas: <una línea>
```

**Fallbacks:** `pypistats` no se usa directo (el archivo ya lo agrega); si la
API HF falla → `sin dato`; si `gh api` no está autenticado → `sin dato`.
**Nunca escribas un número estimado.**

**Verify**:
```bash
make doctor                                     # exit 0
git diff --stat docs/adoption-review.md         # solo ese archivo (más index.html si Step 1)
```
Commit: `docs(distribution): registro de adopción <AAAA-MM-DD>`.

---

### Step 6 — Actualizar estado en `docs/launch-pack.md` (opcional, si hubo cambios)

Si verificaste que el autor respondió comentarios nuevos en LinkedIn (no puedes
verlos sin cuenta; solo si el operador te lo indicó), actualiza la tabla de §5
marcando `respondida (fecha)`. **No inventes estados.** Commit:
`docs(distribution): estado de respuestas de leads`.

Si no hubo cambios, omite este step.

---

## 6. Done criteria (todos deben cumplirse)

- [ ] Branch `advisor/107-activacion-lanzamiento` con commits locales (sin push)
- [ ] `.venv/bin/python -m pytest tests/test_ci_config.py -q` → exit 0
- [ ] `make doctor` → exit 0
- [ ] Si hubo token: `grep -c 'name="google-site-verification"' index.html` → `1`
- [ ] `docs/adoption-review.md` tiene una entrada nueva con la fecha de hoy y al menos 3 métricas reales o `sin dato` justificado
- [ ] `git status --short` vacío al terminar
- [ ] Reporte final entregado (formato abajo) **sin valores inventados**

## 7. STOP conditions (detente y reporta, no improvises)

- El árbol de git no está limpio o `main` no está en `056baf7` o posterior.
- No hay `.venv` (no corras `make bootstrap` sin autorización).
- El token de GSC no fue entregado (Step 1 se salta, no es STOP global).
- El schedule diario falla → captura `--log-failed` y STOP (no toques workflows).
- Un issue de lead no existe → STOP (posible drift).
- Un step requiere cuenta externa (LinkedIn/GSC UI/Cloudflare/Zenodo).
- Una verificación falla dos veces tras un intento razonable.

## 8. Reporte final (formato exacto)

```
Branch: advisor/107-activacion-lanzamiento
Commits: <hash> <mensaje> [; <hash> <mensaje>]
Step 0 (baseline): ok | STOP: <motivo>
Step 1 (GSC meta): hecho | saltado (sin token) | archivo | DNS (operador)
Step 2 (sitemap): índice ok; hijos 200/200/200 | <detalle>
Step 3 (issues): #107 #108 #109 OPEN con labels | sin acceso a gh
Step 4 (schedule): success + Publish success | falló: <primer error>
Step 5 (adopción): PyPI <X> | HF <Y> | GH <Z> | GSC sin dato
Step 6 (launch pack): actualizado | omitido
Pendiente operador: <lista concreta>
```

## 9. Apéndice — glosario para el agente

- **GSC**: Google Search Console, la consola de Google para indexación.
- **Sitemap**: XML que lista las URLs del sitio para que Google las rastree.
- **HF**: Hugging Face Hub, espejo de datos del proyecto (21 subsets).
- **Issue de lead**: pedido de dataset nacido de un comentario de LinkedIn.
- **Schedule**: ejecución automática diaria del pipeline (cron 10:00 UTC).
- **Gate**: verificación que debe quedar en verde (`make doctor`, pytest).
- **Artefacto**: archivo generado por el pipeline en `data/normalized/`.

## 10. Apéndice — dónde mirar si algo no cuadra

| Duda | Documento |
|:---|:---|
| Cómo funciona el repo y sus reglas | `AGENTS.md` (raíz) |
| Índice de navegación y mapa de archivos | `SOURCE_OF_TRUTH.md` |
| Criterios para aceptar un dataset | `docs/dataset-inclusion-criteria.md` |
| Baseline y umbrales de adopción | `docs/adoption-review.md` |
| Material de difusión y leads | `docs/launch-pack.md` |
| Estado del pipeline | `data/normalized/hub_health.md` |

---

*Handoff generado para ejecución autónoma. Si algo de este documento no coincide
con el repo, gana el repo: STOP y reporta.*
