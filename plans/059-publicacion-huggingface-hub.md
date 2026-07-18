# Plan 059: Publicación del bundle en Hugging Face Hub (canal de descubrimiento)

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 6bf6b08..HEAD -- .github/workflows/pypi-release.yml data/dataset_catalog_config.json data/normalized/artifact_manifest.json README.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (nuevo servicio externo + secret nuevo; mitigado: job aislado, dry-run local, no bloquea releases)
- **Depends on**: none hard. Recomendado: plan 052 (señal de adopción) landeado antes para tener baseline pre-HF; no es gate.
- **Category**: direction
- **Planned at**: commit `6bf6b08`, 2026-07-18

## Why this matters

La decisión de producto 2026-07-14 ("construir capacidad por delante de la
demanda") declara: **distribución = alcance = demanda**. El plan 051 construye
la capa de acceso HTTP/DCAT genérica, pero Hugging Face Hub es donde la
audiencia data-science/ML *descubre* datasets tabulares hoy. Los Parquet ya
existen (`data/normalized/*.parquet`, 19 capas publicables, 19/19 con
`redistribution_ok: true`); publicarlos en HF es un job de CI sin dependencias
nuevas en el paquete, y entrega paridad de "una línea":
`datasets.load_dataset("cortega26/chile-hub", "comunas")` ≈
`hub.load_polars("comunas")`. Grep verificado: no existe mención a HF/Kaggle/
conda-forge en el repo.

## Current state

- `.github/workflows/pypi-release.yml` — corre tras "Pipeline Check" exitoso en
  `main` (`workflow_run`) o `workflow_dispatch`. Job `release`: (1) baja el
  artefacto verificado `pipeline-output-$run_id` a `data/normalized/` (L46–68,
  patrón `gh run download`), (2) valida provenance publication-grade (L70–111),
  (3) semantic-release + push tag (L113–155), (4) build + publish PyPI
  (L157–168), (5) **adjunta assets al GitHub Release** (L170–187):

  ```yaml
      - name: Attach verified data assets to release
        if: steps.semantic-release.outputs.released == 'true' && steps.pipeline-assets.outputs.ready == 'true'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          ...
          gh release upload "$tag" \
            data/normalized/chile-hub-publishable-bundle.zip \
            data/normalized/chile-hub-publishable-bundle.zip.sha256 \
            data/normalized/artifact_manifest.json \
            data/normalized/dataset_catalog.json \
            data/normalized/hub_bundle.json \
            --clobber
  ```

- `data/normalized/` contiene `{dataset}.parquet` + `{dataset}.json` para las
  19 capas publicables (las que tienen `outputs` en el catálogo), más
  `datapackage.json`, `dataset_catalog.json`, `artifact_manifest.json` (55
  archivos con sha256). El carril `candidate` (`delincuencia_comunal`,
  `autoridades_locales`) **no** tiene `outputs` ni parquet — queda excluido por
  construcción.
- `data/dataset_catalog_config.json` — 21 entradas con `reuse_policy`
  (`redistribution_ok`) y `outputs` (ver estructura en el excerpt del plan 058;
  aquí basta: `cfg.get("outputs")` truthy ⇒ publicable).
- Convención de workflows: actions pinneadas por SHA con comentario de versión
  (`actions/checkout@9c091bb2… # v7.0.0`), Python 3.13, `uv` vía
  `astral-sh/setup-uv`, permisos mínimos declarados.
- Tests de workflows/guardrails de texto viven en `tests/test_ci_config.py`
  (docstring documenta el incidente que motiva cada guardrail — seguir ese
  patrón).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Build local (artefactos) | `make build` | exit 0, `data/normalized/` regenerado |
| Dry-run del script | `./.venv/bin/python scripts/publish_hf_dataset.py --dry-run` | exit 0, lista 19 parquet + card |
| Tests | `./.venv/bin/pytest tests/test_ci_config.py -v` | all pass |
| Lint | `make lint && make format-check` | exit 0 |
| YAML sanity | `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/pypi-release.yml'))"` ¹ | exit 0 |

¹ Si `yaml` no está instalado en el venv, validar con
`npx --yes yaml-lint` o simplemente `git diff --check` + revisión; NO instalar
paquetes nuevos al venv del proyecto para esto.

## Suggested executor toolkit

- Documentación de referencia (leer antes de Step 3):
  `https://huggingface.co/docs/huggingface_hub/guides/upload` —
  `HfApi.upload_folder`, `create_repo(..., repo_type="dataset", exist_ok=True)`.

## Scope

**In scope** (the only files you should modify/create):
- `scripts/publish_hf_dataset.py` (crear)
- `.github/workflows/pypi-release.yml` (agregar job `hf-publish`)
- `docs/hf/dataset-card.md` (crear — plantilla de la tarjeta)
- `tests/test_ci_config.py` (guardrails de texto del nuevo job)
- `AGENTS.md` (§9 CI/CD: párrafo breve del nuevo job; §11: comando dry-run)
- `README.md` (opcional, Step 6: badge HF junto a los badges existentes)

**Out of scope** (do NOT touch, even though they look related):
- `pyproject.toml` — `huggingface_hub` NO se agrega como dependencia del
  proyecto; se instala solo en CI (`uv pip install` en el job).
- `.github/workflows/pipeline-check.yml` — el job vive en `pypi-release.yml`.
- `src/` (nada de código del paquete; el paquete no debe saber que HF existe).
- Carril `candidate` (`delincuencia_comunal`, `autoridades_locales`) — jamás se
  sube a HF.
- El plan 051 (HTTP estático/DCAT) — canal complementario, no tocar sus archivos.

## Git workflow

- Branch: `advisor/059-huggingface-publish`
- Conventional commits: `feat(ci): publica bundle en Hugging Face Hub tras release`,
  `docs(hf): plantilla de dataset card`, `test(ci): guardrails del job hf-publish`.
- No pushear ni abrir PR salvo instrucción del operador.
- **Secret manual prerequisite (humano, fuera del executor)**: el mantenedor
  debe crear un HF token con scope `write` y guardarlo como secret
  `HF_TOKEN` en GitHub. El plan funciona sin él (dry-run); el job falla
  informativamente si el secret falta.

## Steps

### Step 1: Script `scripts/publish_hf_dataset.py` con `--dry-run`

Crea el script (stdlib + import perezoso de `huggingface_hub`). Contrato:

- Constantes: `ROOT_DIR`, `NORMALIZED_DIR = ROOT_DIR/"data"/"normalized"`,
  `CATALOG_PATH = ROOT_DIR/"data"/"dataset_catalog_config.json"`,
  `CARD_TEMPLATE_PATH = ROOT_DIR/"docs"/"hf"/"dataset-card.md"`.
- `select_publishable_files() -> list[Path]`: lee el catálogo; para cada clave
  con `outputs` truthy **y** `reuse_policy.redistribution_ok is True`, exige
  que exista `data/normalized/{clave}.parquet`; agrega además
  `datapackage.json`, `dataset_catalog.json`, `artifact_manifest.json`.
  Falla con `SystemExit` si alguna capa publicable carece de parquet (drift) o
  si el conteo difiere del esperado por el manifiesto.
- `build_staging_dir(dest)`: copia los parquet bajo `dest/data/` y los JSON de
  catálogo en `dest/`; genera `dest/README.md` desde la plantilla (Step 2)
  reemplazando `{{DATASET_TABLE}}` por una tabla Markdown
  `| Dataset | Filas aprox. | Licencia |` construida desde el catálogo
  (`expected_record_count`, `reuse_policy.license`).
- `main()`: `--dry-run` imprime el árbol staging y sale 0. Sin `--dry-run`:
  requiere `--repo-id` (p. ej. `cortega26/chile-hub`) y env `HF_TOKEN`;
  `create_repo(repo_id, repo_type="dataset", exist_ok=True)` +
  `upload_folder(folder_path=staging, repo_id=repo_id, repo_type="dataset",
  commit_message="chore(data): publish chile-hub <version>")` (versión leída de
  `pyproject.toml` vía `tomllib`, patrón ya usado en
  `.github/workflows/pypi-release.yml` L119). Si `huggingface_hub` no
  importa → `SystemExit("instala con: pip install huggingface_hub")`.

**Verify**: `make build && ./.venv/bin/python scripts/publish_hf_dataset.py --dry-run`
→ exit 0; la salida lista exactamente 19 `data/*.parquet` + 3 JSON + README.md.
Y: `./.venv/bin/python scripts/publish_hf_dataset.py --dry-run | grep -c "data/.*\.parquet"` → `19`

### Step 2: Plantilla `docs/hf/dataset-card.md`

Crea la plantilla con frontmatter YAML de HF dataset card:

```markdown
---
license: other
pretty_name: chile-hub — Datos públicos de Chile curados
language: [es]
tags: [chile, open-data, government, tabular, parquet]
size_categories: [100K<n<1M]
---

# chile-hub

Datos públicos de Chile curados, normalizados y validados — 19 capas
(DPA, Censo 2024, indicadores económicos, salud, educación, finanzas
municipales, electoral y más). Espejo en Hugging Face Hub del bundle oficial
publicado en GitHub Releases: https://github.com/cortega26/chile-hub

## Uso

\`\`\`python
from datasets import load_dataset
comunas = load_dataset("cortega26/chile-hub", data_files="data/comunas.parquet")
\`\`\`

## Capas y licencias

{{DATASET_TABLE}}

Cada capa documenta su fuente y licencia en
https://github.com/cortega26/chile-hub/tree/main/docs/datasets — atribución
requerida según la licencia de cada fuente (ver DATA_LICENSES.md).
```

(Nota para el executor: `license: other` porque las capas mezclan CC BY,
"libre con citación" BCCh, etc.; la tabla por dataset es la fuente fina.)

**Verify**: `grep -c "{{DATASET_TABLE}}" docs/hf/dataset-card.md` → `1`

### Step 3: Job `hf-publish` en `pypi-release.yml`

Agrega un job **después** de `release`:

```yaml
  hf-publish:
    name: Publish dataset to Hugging Face Hub
    needs: release
    if: needs.release.outputs.released == 'true'  # ver nota de outputs abajo
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
      - uses: astral-sh/setup-uv@d31148d669074a8d0a63714ba94f3201e7020bc3 # v8.3.0
      - name: Download verified pipeline data assets
        # Replica el patrón del job release (L46–68): gh run download del
        # artefacto pipeline-output-$run_id hacia data/normalized/.
      - name: Publish to Hugging Face Hub
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          uv pip install --system huggingface_hub
          python scripts/publish_hf_dataset.py --repo-id cortega26/chile-hub
```

Notas de implementación para el executor: (a) el job `release` hoy no expone
`outputs`; agrégalos (`outputs: released: ${{ steps.semantic-release.outputs.released }}`)
y referencia `needs.release.outputs.released`. (b) El download del artefacto
debe repetir la lógica de `run_id` del job `release` (workflow_run id o último
exitoso en main) — copia ese bloque verbatim. (c) Si `HF_TOKEN` no está
definido, el paso de publish debe fallar con mensaje claro, no con stacktrace:
`if [ -z "$HF_TOKEN" ]; then echo "::error::secret HF_TOKEN no configurado"; exit 1; fi`.
(d) Este job NO debe bloquear el release: es el último en la cadena `needs` y
ningún otro job depende de él.

**Verify**: `python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/pypi-release.yml')); assert 'hf-publish' in d['jobs']; assert d['jobs']['hf-publish']['needs']=='release'; print('job ok')"` → `job ok`
(si `yaml` no está disponible: `grep -c "hf-publish:" .github/workflows/pypi-release.yml` → `1` y revisión manual del YAML indentado)

### Step 4: Guardrails en `tests/test_ci_config.py`

Agrega una clase `HfPublishJobGuardrailTests` con docstring que documente la
motivación (canal de distribución HF agregado 2026-07; regresiones a evitar:
que el job desaparezca silenciosamente, que suba datasets del carril candidate,
que pase a bloquear el release). Tests de texto simple (patrón del archivo):

1. El workflow contiene `hf-publish:` y `secrets.HF_TOKEN`.
2. El script `scripts/publish_hf_dataset.py` existe y contiene
   `redistribution_ok` y `--dry-run`.
3. El workflow NO contiene `delincuencia_comunal` ni `autoridades_locales`
   (el candidate lane jamás se nombra en la publicación HF).
4. Ningún otro job del workflow declara `needs: [hf-publish]` ni
   `needs: release` adicional que convierta a hf-publish en bloqueante
   (chequeo de texto: `hf-publish` aparece solo como definición de job y en su
   propio bloque).

**Verify**: `./.venv/bin/pytest tests/test_ci_config.py -v` → all pass (4+ nuevos)

### Step 5: Documentar en `AGENTS.md`

- §9 (CI/CD): agrega al final del párrafo de jobs del workflow de release una
  línea: "Tras cada release, el job `hf-publish` de `pypi-release.yml` replica
  las 19 capas publicables (Parquet + catálogo) a Hugging Face Hub
  (`cortega26/chile-hub`, requiere secret `HF_TOKEN`); nunca incluye el carril
  `candidate` y no bloquea el release si falla."
- §11 (comandos): agrega
  `./.venv/bin/python scripts/publish_hf_dataset.py --dry-run   # Simula la publicación HF (sin subir nada)`.

**Verify**: `grep -c "hf-publish" AGENTS.md` → ≥2

### Step 6 (opcional, recomendado): Badge en README

Agrega junto a los badges existentes de README (zona L43–52, fuera de cualquier
bloque delimitado):
`[![Hugging Face](https://img.shields.io/badge/🤗%20Datasets-chile--hub-yellow)](https://huggingface.co/datasets/cortega26/chile-hub)`

**Verify**: `python scripts/sync_docs.py --check` → exit 0 (el badge no toca
bloques delimitados, no debe romper el check)

## Test plan

- Los 4 guardrails de Step 4 en `tests/test_ci_config.py` (patrón: tests de
  texto existentes en ese archivo, p. ej. `SinimDailyJobGuardrailTests`).
- Verificación funcional = dry-run de Step 1 (no hay test de subida real: HF
  queda fuera de la suite, igual que PyPI).
- `./.venv/bin/pytest tests/test_ci_config.py -v` → all pass.

## Done criteria

- [ ] `make build && ./.venv/bin/python scripts/publish_hf_dataset.py --dry-run` exit 0, lista 19 parquet
- [ ] El dry-run NO lista `delincuencia_comunal` ni `autoridades_locales`
- [ ] `docs/hf/dataset-card.md` existe con placeholder `{{DATASET_TABLE}}`
- [ ] `pypi-release.yml` tiene job `hf-publish` con `needs: release`, `secrets.HF_TOKEN`, y outputs expuestos en `release`
- [ ] `./.venv/bin/pytest tests/test_ci_config.py -v` exit 0
- [ ] `make lint && make format-check` exit 0
- [ ] `python scripts/sync_docs.py --check` exit 0
- [ ] No files outside the in-scope list are modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) si:

- Alguna de las 19 capas publicables tiene `reuse_policy.redistribution_ok`
  distinto de `True` o `status` distinto de publicable (la premesa legal del
  plan queda inválida → NO subir, reportar).
- El maintainer aún no crea el secret `HF_TOKEN` y se te pide "dejarlo andando"
  — el entregable del plan es CI + script; la primera subida real requiere el
  secret (documentar en el PR que el primer release con HF ocurrirá cuando el
  secret exista).
- `pypi-release.yml` difiere del excerpt (p. ej. el job `release` ya tiene
  `outputs` o cambió el mecanismo de descarga del artefacto).
- `huggingface_hub` requiriese agregarse a `pyproject.toml` para que el script
  funcione en CI (no debería: se instala con `uv pip install --system` en el
  job; si eso no funciona en el runner, reportar en vez de tocar deps).
- Un step falla dos veces tras un intento razonable de fix.

## Maintenance notes

- **Cuando cambie el set de capas publicables** (dataset nuevo promovido a
  `stable_publishable`, o uno deprecado), el script lo recoge automáticamente
  del catálogo — pero la tabla de la dataset card solo se regenera en la
  próxima publicación. Sin acción manual.
- La estrategia de versionado en HF: `upload_folder` con commit por release deja
  historia de commits en el repo-dataset; NO configurar revisiones/tags HF en
  v1 (follow-up posible: taggear `v{version}` en HF para reproducibilidad —
  queda explícitamente diferido).
- Interacción con plan 052: una vez HF esté live, agregar `downloads` del API
  de HF (`/api/datasets/{repo}`) como fuente adicional del script de señal de
  adopción — follow-up natural, fuera de scope aquí.
- Interacción con plan 051: HF es canal de *descubrimiento*; la capa HTTP
  estática/DCAT sigue siendo la capa de *acceso* canónica. No fusionar.
- En review, escrutar: que el job no pueda subir nada sin provenance
  publication-grade (hereda el gate del artefacto que descarga), y que el
  candidate lane esté excluido por construcción (ausencia de `outputs`), no por
  una lista hardcodeada que pueda quedar stale.
