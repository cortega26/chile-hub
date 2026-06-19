# Plan 016: Cache de staging en CI para acelerar ejecuciones diarias

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat a2cd288..HEAD -- .github/workflows/pipeline-check.yml`
> If the workflow file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: MED
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `a2cd288`, 2026-06-19

## Why this matters

El pipeline de CI diario (`schedule` a las 10:00 UTC) ejecuta los 11 extractores
secuencialmente en cada corrida, re-descargando datos de APIs gubernamentales que
en su mayoría no cambian a diario. Esto consume ~5-15 minutos de CI por ejecución
y genera tráfico innecesario hacia las fuentes. De los 15 datasets, solo los
indicadores económicos (BCCh) y potencialmente RES (empresas mensuales) cambian
con frecuencia diaria o semanal; los demás (división territorial, censo,
distritos electorales, establecimientos) se actualizan trimestral o anualmente.

Agregar un cache de `data/staging/` con TTL de 24 horas permitiría saltar la
extracción para la mayoría de los datasets en ejecuciones `schedule`, reduciendo
el tiempo de CI y la carga sobre las APIs fuente.

## Current state

### Archivo relevante

- `.github/workflows/pipeline-check.yml` — workflow principal de CI

### Workflow actual

El job `build-and-test` ejecuta los extractores secuencialmente (líneas 91-104):
```yaml
- name: Extract source data
  if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
  run: |
    python src/extractors/subdere_extractor.py
    python src/extractors/bcentral_extractor.py
    python src/extractors/censo_extractor.py
    python src/extractors/censo_hogares_viviendas_extractor.py
    python src/extractors/salud_extractor.py
    python src/extractors/electoral_extractor.py
    python src/extractors/mineduc_establecimientos_extractor.py
    python src/extractors/sinim_finanzas_extractor.py
    python src/extractors/mineduc_resultados_extractor.py
    python src/extractors/siedu_extractor.py
    python src/extractors/res_extractor.py
```
No hay cache de `data/staging/` ni `data/raw/`.

El workflow ya usa `actions/cache` con SHA pinning (v5) para:
- Dependencias pip vía `setup-python` (cache: pip integrado)
- Chromium de Playwright (línea 229, `actions/cache@27d5ce7...` # v5.0.5)

### Datasets por frecuencia de cambio

| Frecuencia | Datasets |
|-----------|----------|
| Diaria | `indicadores` (BCCh) |
| Mensual | `empresas` (RES), `establecimientos_salud` (MINSAL) |
| Trimestral/Anual | `finanzas_municipales`, `resultados_educacionales`, `indicadores_urbanos_siedu` |
| Muy rara | `regiones`, `provincias`, `comunas`, `censo_comunal`, `censo_hogares_viviendas`, `distritos_electorales`, `establecimientos_educacionales`, `perfil_territorial_comunal`, `comunas_enriquecidas` |

### Convenciones del repo

- CI usa `actions/cache` con SHA pinning (v5) y keys basadas en hash de `requirements.txt`.
- Workflow dispatch manual con `publish=true` para publicación.
- Los extractores guardan snapshots en `data/raw/` y staging en `data/staging/`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Validate workflow YAML | `python -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml')); print('YAML válido')"` | exit 0, "YAML válido" |

## Scope

**In scope**:
- `.github/workflows/pipeline-check.yml` — agregar steps `Set date key`, `Cache staging data`, y modificar `Extract source data` para que sea condicional

**Out of scope** (do NOT touch):
- `Makefile` — no modificar
- `src/extractors/` — no modificar extractores
- Otros workflows (`.github/workflows/pypi-release.yml`)

## Git workflow

- Branch: `advisor/016-ci-staging-cache`
- Commit único; mensaje estilo `perf(ci): add staging data cache for daily runs`
- No hacer push ni abrir PR a menos que se indique.

## Steps

### Step 1: Agregar step para generar clave de fecha diaria

En `.github/workflows/pipeline-check.yml`, en el job `build-and-test`, AGREGAR
un step ANTES del step `Extract source data`. Insertarlo después del paso
`Install unrar` y antes de `Extract source data`:

```yaml
- name: Set date key
  id: date-key
  if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
  run: echo "stamp=$(date +%Y-%m-%d)" >> "$GITHUB_OUTPUT"
```

Esto genera una clave de fecha (e.g. `2026-06-19`) usable en el step de cache.
`github.run_date` NO existe en GitHub Actions — por eso usamos `date +%Y-%m-%d`.

### Step 2: Agregar step de cache para staging

En el mismo job, AGREGAR un step después del `Set date key` y antes de `Extract
source data`:

```yaml
- name: Cache staging data
  id: cache-staging
  if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
  uses: actions/cache@27d5ce7f107fe9357f9df03efb73ab90386fccae # v5.0.5
  with:
    path: |
      data/staging/
      data/raw/
    key: staging-data-${{ steps.date-key.outputs.stamp }}-${{ hashFiles('.github/workflows/pipeline-check.yml') }}
    restore-keys: |
      staging-data-${{ steps.date-key.outputs.stamp }}-
      staging-data-
```

Nota: se usa `actions/cache@27d5ce7...` (v5.0.5, SHA pinning) para seguir la
convención del repo (misma versión que el cache de Chromium en línea 229).

### Step 3: Modificar el paso de extractores para usar el cache

Reemplazar el step `Extract source data` por una versión condicional que solo
ejecute extractores de alta frecuencia si el cache existe:

```yaml
- name: Extract source data (conditional)
  if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
  run: |
    if [ "${{ steps.cache-staging.outputs.cache-hit }}" = "true" ]; then
      echo "Cache de staging encontrado. Ejecutando solo extractores de alta frecuencia..."
      python src/extractors/bcentral_extractor.py
      python src/extractors/res_extractor.py
      # Los demás extractores usan datos cacheados de data/staging/ y data/raw/
    else
      echo "Cache no encontrado. Ejecutando extracción completa..."
      python src/extractors/subdere_extractor.py
      python src/extractors/bcentral_extractor.py
      python src/extractors/censo_extractor.py
      python src/extractors/censo_hogares_viviendas_extractor.py
      python src/extractors/salud_extractor.py
      python src/extractors/electoral_extractor.py
      python src/extractors/mineduc_establecimientos_extractor.py
      python src/extractors/sinim_finanzas_extractor.py
      python src/extractors/mineduc_resultados_extractor.py
      python src/extractors/siedu_extractor.py
      python src/extractors/res_extractor.py
    fi
```

**Verify**: Validar sintaxis YAML:

```
python -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml')); print('YAML válido')"
```

## Test plan

No aplican tests locales — este plan modifica solo CI. La verificación es:

1. Push a una branch de prueba.
2. Ejecutar el workflow manualmente vía `workflow_dispatch`.
3. Verificar en el log de CI que:
   - El step "Cache staging data" muestra `cache-hit: false` en la primera corrida.
   - La segunda corrida (mismo día) muestra `cache-hit: true`.
   - Con cache-hit, solo se ejecutan `bcentral_extractor.py` y `res_extractor.py`.
   - `python scripts/verify_pipeline.py` y `python -m pytest` completan exitosamente en ambos casos.

## Done criteria

- [ ] El archivo `.github/workflows/pipeline-check.yml` es YAML válido
- [ ] El step `Set date key` está presente antes de `Cache staging data`
- [ ] El step `Cache staging data` está presente antes de `Extract source data (conditional)`
- [ ] El step `Extract source data (conditional)` usa el output `steps.cache-staging.outputs.cache-hit`
- [ ] Con cache-hit: solo se ejecutan `bcentral_extractor.py` y `res_extractor.py`
- [ ] Sin cache-hit: se ejecutan los 11 extractores completos
- [ ] `python scripts/verify_pipeline.py` y `python -m pytest` pasan en ambos casos
- [ ] No files outside the in-scope list are modified (`git diff --stat`)

## STOP conditions

Stop and report back (do not improvise) if:

- El workflow YAML no es válido según `python -c "import yaml; ..."`.
- El step `Set date key` no produce la salida esperada en CI (el cache key
  usa `steps.date-key.outputs.stamp` — si `date +%Y-%m-%d` no está disponible,
  usar `$(date -u +%Y-%m-%d)` como alternativa).
- El cache incluye archivos que no deberían persistir entre runs (ej. timestamps
  en metadata.json que causan falsos positivos en verificación de frescura).
- Un step de verificación falla dos veces tras un intento razonable de corrección.

## Maintenance notes

- El cache usa `steps.date-key.outputs.stamp` (fecha YYYY-MM-DD) como parte de la
  key, lo que resulta en TTL de 24 horas. Si se necesita invalidar el cache antes,
  cambiar el workflow file (el hash del YAML es parte de la key) o despachar
  manualmente.
- Si se agregan nuevos extractores de alta frecuencia, agregarlos al bloque
  condicional del Step 3.
- GitHub Actions cache tiene un límite de 10GB por repo. `data/staging/` son
  ~60MB, muy por debajo del límite.
- GitHub evicta caches no accedidos por 7 días. Como el schedule es diario, el
  cache se renovará cada día.
