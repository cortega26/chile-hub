# Plan 107: Handoff de activación de lanzamiento (agente autónomo)

> **Para un agente pequeño (Cowork) ejecutando solo.** Cada step trae comando,
> resultado esperado, fallback y condición de STOP. No improvises fuera del
> scope. Al terminar, reporta con el formato de la sección "Reporte".
>
> **Drift check (primero)**: `git log --oneline -3` y `git status --short`.
> Si el árbol no está limpio o `main` no está en `52d41dd` o posterior, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW (solo docs/config; no toca datos ni workflows)
- **Category**: distribution / handoff
- **Planned at**: commit `52d41dd`, 2026-09-26

## Objetivo

Ejecutar las acciones de activación que **no requieren cuentas externas**:
verificación de Search Console por meta tag, verificación del primer schedule
diario tras las reparaciones, y registro del baseline de adopción. Lo que
requiere LinkedIn/HN/Cloudflare/GSC-UI lo hace el operador (fuera de scope).

## Reglas de seguridad (obligatorias)

1. **No push ni merge.** Trabaja en branch `advisor/107-activacion-lanzamiento`,
   commit local, y deja el push para el operador.
2. **No tocar cuentas externas.** Nada de LinkedIn, HN, Google, Cloudflare,
   Zenodo. Si un step lo requiere, es del operador.
3. **No inventar valores.** Si una métrica o token no está disponible, se
   registra `sin dato` y se sigue (nunca un número estimado).
4. **Secretos**: el token de verificación de Google es público (va en el HTML),
   pero si el operador no lo entregó, **STOP** en ese step — no inventes ni
   uses un token de ejemplo.
5. Un fallo de verificación dos veces = STOP y reporte (no parches a ciegas).

## Scope

**In scope**:
- `index.html` (meta tag de verificación, solo si el token está)
- `docs/adoption-review.md` (entrada de registro con métricas reales)
- `docs/launch-pack.md` (estado verificado de respuestas/leads)

**Out of scope**:
- Publicar en redes, enviar el sitemap en la UI de GSC, tocar DNS/Cloudflare.
- Cambios a workflows, extractores, datos o validaciones.
- Issues nuevos: los leads ya están en #107/#108/#109.

## Steps

### Step 0: Baseline

```bash
git checkout -b advisor/107-activacion-lanzamiento
./.venv/bin/pytest tests/test_ci_config.py -q -k "HttpAccess or Citation"
```
**Esperado**: branch creado, tests verdes. Si fallan sin tocar nada, STOP.

### Step 1: Verificación de Google Search Console (meta tag)

**Prerrequisito**: el operador entrega el token (`google-site-verification`).
Si no está, registrar "sin dato" y **saltar al Step 3** (no bloquea el resto).

1. Insertar en `index.html`, dentro de `<head>` (junto a los otros `<meta>`):
   ```html
   <meta name="google-site-verification" content="TOKEN_EXACTO" />
   ```
2. **Verify**:
   ```bash
   grep -c 'name="google-site-verification"' index.html   # → 1
   make verify-landing                                     # → passed
   make doctor                                             # → exit 0
   ```
3. Commit: `feat(seo): verificación de Google Search Console (meta tag)`.

**Fallbacks**:
- Si el operador eligió **archivo HTML** (`googleXXXX.html`): crear el archivo
  en la raíz del repo con el contenido exacto que entregue Google, verificar
  `test -f google*.html`, correr `make doctor` y commitear.
- Si eligió **DNS TXT**: es acción de Cloudflare → documentar en el commit del
  Step 3 y STOP en este step (no hay nada que hacer en el repo).

### Step 2: Verificar el sitemap en vivo (pre-submit)

```bash
curl -s https://tooltician.com/chile-hub/sitemap.xml | head -5
curl -s -o /dev/null -w "%{http_code}\n" https://tooltician.com/chile-hub/sitemap-pages.xml
curl -s -o /dev/null -w "%{http_code}\n" https://tooltician.com/chile-hub/reference/sitemap.xml
curl -s -o /dev/null -w "%{http_code}\n" https://tooltician.com/chile-hub/comunas/sitemap.xml
```
**Esperado**: el índice empieza con `<sitemapindex` y los 3 hijos responden 200.
**Fallback**: si un hijo da 404, anotarlo en el reporte y NO tocar nada (puede
ser timing de Pages Deploy); reintentar una vez a los 5 minutos.

### Step 3: Verificar issues de leads

```bash
gh issue view 107 --json title,labels --jq '{title, labels: [.labels[].name]}'
gh issue view 108 --json title,labels --jq '{title, labels: [.labels[].name]}'
gh issue view 109 --json title,labels --jq '{title, labels: [.labels[].name]}'
```
**Esperado**: los 3 existen con labels `enhancement` y `dataset`.
**Fallback**: si `gh` no está autenticado, registrar "sin acceso a gh" y seguir
(no crear nada a mano). Si un issue falta, STOP y reporte.

### Step 4: Verificar el primer schedule diario

```bash
gh run list --workflow pipeline-check.yml --event schedule --limit 3 \
  --json conclusion,createdAt,url --jq '.[] | "\(.createdAt[:16]) \(.conclusion) \(.url)"'
```
**Esperado**: el run más reciente del schedule (10:00 UTC) en `success`.
Si el más reciente es de ayer (el cron aún no corrió hoy), esperar y repetir
una vez.

Si el run es `success`, confirmar que publicó y actualizó HF:
```bash
RUN=$(gh run list --workflow pipeline-check.yml --event schedule --limit 1 --json databaseId --jq '.[0].databaseId')
gh run view "$RUN" --json jobs --jq '.jobs[] | "\(.name): \(.conclusion)"'
```
**Esperado**: `Publish verified data: success`.

**Fallback si falla**:
```bash
gh run view "$RUN" --log-failed 2>/dev/null | grep -E "##\[error\]|Traceback" | tail -20
```
Guardar la salida en el reporte y **STOP** (no arreglar código sin plan).

### Step 5: Registro de adopción

Ejecutar los comandos de `docs/adoption-review.md` → "Cómo leer las métricas".
Luego **append** una entrada fechada en la sección "Registro", con este formato:

```markdown
### AAAA-MM-DD — revisión (agente)

- PyPI (mes/semana): X / Y — fuente: `data/normalized/adoption.json`
- HF: descargas X, likes Y — fuente: API HF
- GitHub: stars X, forks Y — fuente: API GitHub
- Search Console: `sin dato` (pendiente operador) | impresiones /comunas/: X
- Issues de leads: #107, #108, #109 (estado)
- Notas: <una línea con lo relevante>
```

**Fallbacks**: `pypistats` 403/rate-limit → usar `adoption.json`; API HF con
error → `sin dato`; `gh api` sin auth → `sin dato`. Nunca estimar.

**Verify**: `make doctor` exit 0 y `git diff --stat` limitado a
`docs/adoption-review.md` (+ lo del Step 1 si aplicó).

### Step 6: Actualizar launch pack y commit final

- En `docs/launch-pack.md` §5, marcar el estado verificado de las respuestas
  del post (la vista pública de LinkedIn no muestra todas las respuestas
  anidadas; anotar "verificado/por confirmar" con la fecha).
- Commit: `docs(distribution): registro de activación <fecha>`.
- **No push**.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `git status --short` limpio al final (todo commiteado en el branch)
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -q` exits 0
- [ ] `make doctor` exits 0
- [ ] Si hubo token: `grep -c 'google-site-verification' index.html` == 1
- [ ] `docs/adoption-review.md` tiene una entrada con la fecha de hoy y al menos 3 métricas reales (o `sin dato` justificado)
- [ ] Reporte entregado (sección siguiente) sin inventar valores

## STOP conditions

Stop and report (do not improvise) if:

- El token de verificación no fue entregado (Step 1) → saltar, no inventar.
- El schedule diario falla → capturar log y STOP (no tocar workflows).
- `gh` no está autenticado y no se pueden verificar issues o runs → registrar y STOP parcial.
- Cualquier step requiere una cuenta externa (LinkedIn, GSC UI, Cloudflare).
- Una verificación falla dos veces tras un intento razonable.

## Reporte (formato de salida del agente)

```
Branch: advisor/107-activacion-lanzamiento
Commits: <hash> <mensaje>
Step 1 (GSC meta): hecho | saltado (sin token) | DNS pendiente operador
Step 2 (sitemap): 200/200/200/200 | <detalle>
Step 3 (issues): #107 #108 #109 ok | <detalle>
Step 4 (schedule): success | falló: <primer error>
Step 5 (adopción): PyPI X | HF Y | GH Z | GSC sin dato
Pendiente operador: <lista>
```

## Maintenance notes

- Cuando el operador registre GSC y haya 2–4 semanas de impresiones, actualizar
  los umbrales de `docs/adoption-review.md` con datos reales.
- El post técnico y el Show HN son del operador; este plan no los publica.
