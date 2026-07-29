"""Guardrails de configuración de CI/Make que no son expresables como tests de
Python puro, pero cuya regresión ya causó fallos reales de pipeline.

No parsean el YAML con un parser dedicado (evita depender de un paquete
transitivo como pyyaml que no es dependencia directa del proyecto); usan
comprobaciones de texto simples y suficientes para el guardrail específico.
"""

import json
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from check_companion_paths import check_companions

PIPELINE_CHECK_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "pipeline-check.yml"
MONTHLY_SCRAPE_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "monthly-scrape.yml"
ADOPTION_STATS_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "adoption-stats.yml"
GEOMETRIA_COMUNAL_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "geometria-comunal.yml"
PYPI_RELEASE_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "pypi-release.yml"
MAKEFILE = ROOT_DIR / "Makefile"
MKDOCS_CONFIG = ROOT_DIR / "mkdocs.yml"
DOCS_DIR = ROOT_DIR / "docs"
PUBLISH_HF_SCRIPT = ROOT_DIR / "scripts" / "publish_hf_dataset.py"


class SinimDailyJobGuardrailTests(unittest.TestCase):
    """Regresión: el job diario de Pipeline Check corría
    sinim_finanzas_extractor.py (un stub que siempre escribe 3 filas de
    FALLBACK_ROWS) incondicionalmente, sobrescribiendo el snapshot mensual
    real que Monthly Scrape ya había commiteado a git. finanzas_municipales
    es stable_publishable desde 2026-06-30 (commit ca698ea) y requiere datos
    reales — esto bloqueó "publish" todos los días hasta el fix de 5ba983e.
    """

    def test_pipeline_check_daily_extract_does_not_call_sinim_stub_extractor(self):
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn(
            "src/extractors/sinim_finanzas_extractor.py",
            content,
            "El job diario de Pipeline Check no debe invocar el extractor "
            "stub de SINIM — finanzas_municipales es de cadencia mensual "
            "(ver Monthly Scrape workflow) y su snapshot vive versionado "
            "en git, no se re-extrae cada día.",
        )

    def test_pipeline_check_restores_versioned_sinim_snapshot(self):
        """Guardia positiva: el paso que protege el snapshot mensual de una
        restauración de actions/cache obsoleta sigue presente."""
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Restore versioned SINIM snapshot", content)
        self.assertIn(
            "git checkout -- data/staging/finanzas_municipales.csv "
            "data/staging/finanzas_municipales.metadata.json",
            content,
        )

    def test_makefile_extract_target_does_not_call_sinim_stub_extractor(self):
        content = MAKEFILE.read_text(encoding="utf-8")
        extract_target = _extract_make_target(content, "extract")
        self.assertNotIn("sinim_finanzas_extractor.py", extract_target)

    def test_monthly_scrape_commit_step_force_adds_gitignored_paths(self):
        """Regresión relacionada: el paso de commit del scrape mensual usaba
        `git add` sin `-f` sobre rutas cubiertas por `data/*` en .gitignore,
        lo que abortaba el step bajo `bash -e` sin dejar rastro útil en el
        log (fix en 57e6eaf)."""
        content = MONTHLY_SCRAPE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('git add -f "$path"', content)
        self.assertNotIn('git add "$path"', content)


class AutoridadesElectasScraplingGuardrailTests(unittest.TestCase):
    """Regresión: en el job diario de Pipeline Check (cache-miss → extracción
    completa), autoridades_electas_extractor.py corría con el python del venv
    del job, que no puede incluir scrapling (el extra scraping conflicta con
    dev vía click — ver pyproject.toml). El extractor degradaba a 155 registros
    (155 diputados, 0 senadores) mientras lo publicado tiene 205 (155+50), y el
    paso "Check build-synced files" abortó los schedule de 2026-07-19 y
    2026-07-20 bloqueando el publish diario. Fix: invocar el extractor vía
    `uv run --no-project` (entorno efímero con scrapling).
    """

    def test_daily_extract_uses_ephemeral_scrapling_env_for_autoridades(self):
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        ephemeral_lines = [
            line
            for line in content.splitlines()
            if "autoridades_electas_extractor.py" in line and "uv run --no-project" in line
        ]
        self.assertTrue(
            ephemeral_lines,
            "pipeline-check.yml debe invocar autoridades_electas_extractor.py "
            "vía `uv run --no-project` (entorno efímero con scrapling) — el "
            "venv del job no puede incluirlo (conflicto de click).",
        )
        self.assertIn("scrapling[fetchers]", ephemeral_lines[0])

    def test_no_bare_venv_invocation_of_autoridades_electas_remains(self):
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        bare = [
            line.strip()
            for line in content.splitlines()
            if line.strip() == "python src/extractors/autoridades_electas_extractor.py"
        ]
        self.assertEqual(
            bare,
            [],
            "Queda una invocación directa (venv) de "
            "autoridades_electas_extractor.py — sin scrapling degrada a "
            "155 registros (0 senadores) y rompe el publish diario.",
        )


class MkDocsReferenceSlugGuardrailTests(unittest.TestCase):
    """Regresión: la documentación se publica bajo /reference/ y la página de
    API también se llamaba reference.md, por lo que los enlaces generados desde
    el home terminaban en /reference/reference/. La página de API debe usar un
    slug distinto al directorio publicado.
    """

    def test_api_reference_page_slug_does_not_duplicate_site_dir(self):
        content = MKDOCS_CONFIG.read_text(encoding="utf-8")
        self.assertIn("site_dir: reference", content)
        self.assertIn("- Referencia de API: api.md", content)
        self.assertNotIn("- Referencia de API: reference.md", content)
        self.assertTrue((DOCS_DIR / "api.md").is_file())
        self.assertFalse((DOCS_DIR / "reference.md").exists())


class DependabotWorkflowGuardrailTests(unittest.TestCase):
    """Dependency-only workflow PRs must not require unrelated documentation.

    Dependabot updates action pins across all workflows. The companion checker
    previously required AGENTS.md for pipeline/monthly workflow edits, causing
    PRs #31 and #35 to fail before their actual checks ran.
    """

    def test_action_pin_updates_do_not_require_agents_documentation(self):
        changed_workflows = [
            ".github/workflows/adoption-stats.yml",
            ".github/workflows/monthly-scrape.yml",
            ".github/workflows/pages-deploy.yml",
            ".github/workflows/pipeline-check.yml",
            ".github/workflows/pypi-release.yml",
            ".github/workflows/testpypi.yml",
        ]
        self.assertEqual(check_companions(changed_workflows), [])


class AdoptionBadgeGuardrailTests(unittest.TestCase):
    """The README badge must resolve to a versioned Pages artifact."""

    def test_adoption_workflow_stages_both_published_badge_artifacts(self):
        content = ADOPTION_STATS_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "git add data/normalized/adoption.json data/normalized/adoption_badge.json",
            content,
        )

    def test_adoption_stats_completion_triggers_pages_deploy(self):
        content = (ROOT_DIR / ".github" / "workflows" / "pages-deploy.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('"Adoption Stats (PyPI + GitHub Releases)"', content)

    def test_release_push_is_atomic(self):
        """El push del commit de release y su tag debe ser atomico.

        `git push` no es atomico por defecto: empuja cada ref por separado. Si
        `main` es rechazado por una carrera con otro commit de bot, el tag queda
        publicado igual y bloquea el release de forma permanente —
        semantic-release ve su propio tag y responde "already released" en cada
        run posterior, en verde. Ocurrio el 2026-07-10 con v1.22.0.
        """
        content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("git push --atomic origin HEAD:main", content)
        self.assertNotIn("git push origin HEAD:main", content)

    def test_out_of_band_staging_is_excluded_from_the_freshness_guard(self):
        """El carril candidate no lo construye `make build` (ADR-012), asi que su
        staging no puede disparar el guardian de frescura: seria un falso
        positivo permanente tras cada refresh de CI (Plan 064)."""
        from scripts.verify_pipeline import OUT_OF_BAND_STAGING_METADATA

        self.assertIn("geometria_comunal.metadata.json", OUT_OF_BAND_STAGING_METADATA)

    def test_every_data_committing_workflow_triggers_pages_deploy(self):
        """Todo workflow que commitea datos con GITHUB_TOKEN debe estar en el
        `workflow_run` de Pages.

        Los commits hechos con el GITHUB_TOKEN por defecto no disparan eventos
        `push`, así que sin esta lista Pages nunca redespliega y el sitio sirve
        datos viejos — o un 404, como pasó con el GeoParquet comunal: el
        workflow del Plan 064 commiteó el artefacto y Pages siguió sin servirlo.
        """
        content = (ROOT_DIR / ".github" / "workflows" / "pages-deploy.yml").read_text(
            encoding="utf-8"
        )
        trigger_block = content.split("workflow_dispatch")[0]
        for workflow in (
            "Pipeline Check",
            "PyPI Release",
            "Adoption Stats (PyPI + GitHub Releases)",
            "Refresh Candidate Comunal Geometry",
        ):
            with self.subTest(workflow=workflow):
                self.assertIn(f'"{workflow}"', trigger_block)

    def test_adoption_badge_artifact_exists_and_has_shields_schema(self):
        badge_path = ROOT_DIR / "data" / "normalized" / "adoption_badge.json"
        self.assertTrue(badge_path.is_file(), "Falta el recurso del badge de instalaciones")
        badge = json.loads(badge_path.read_text(encoding="utf-8"))
        self.assertEqual(badge["schemaVersion"], 1)
        self.assertEqual(badge["label"], "instalaciones/mes")


class LandingSyncGateGuardrailTests(unittest.TestCase):
    """El gate real de la landing ("Check build-synced files") solo corre en la
    vía schedule/workflow_dispatch y después de un build completo, así que una
    deriva de index.html queda latente hasta el siguiente run programado — pasó
    con autoridades_locales (#270) y se repitió con geometria_comunal, que
    reventó el publish diario del 2026-07-24 al 26.

    check_landing_sync.py adelanta esa detección a cada push/PR; estos guardrails
    evitan que se desconecte silenciosamente del job rápido o de `make doctor`.
    """

    def test_quality_job_runs_landing_sync_gate(self):
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python scripts/check_landing_sync.py", content)

    def test_doctor_target_runs_landing_sync_gate(self):
        body = _extract_make_target(MAKEFILE.read_text(encoding="utf-8"), "doctor")
        self.assertIn(
            "scripts/check_landing_sync.py",
            body,
            "`make doctor` debe correr el gate de landing antes de commit.",
        )


class GeometriaCandidateWorkflowGuardrailTests(unittest.TestCase):
    """La geometría comunal es candidate y supera el límite local de 500 KB.

    Su publicación debe pasar por un workflow manual que valide el GeoParquet
    antes de forzar exclusivamente los artefactos permitidos. Esto preserva el
    guard de archivos grandes y evita que la geometría entre por accidente al
    build diario o al bundle estable.
    """

    def setUp(self):
        self.content = GEOMETRIA_COMUNAL_WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_is_manual_only_with_locked_pipeline_dependencies(self):
        self.assertIn("workflow_dispatch:", self.content)
        self.assertNotIn("schedule:", self.content)
        self.assertIn("contents: write", self.content)
        self.assertIn("uv lock --locked", self.content)
        self.assertIn("uv sync --extra pipeline --extra dev --locked", self.content)

    def test_validates_standalone_builder_before_commit(self):
        build_index = self.content.index("scripts/build_geometria_comunal.py")
        validation_index = self.content.index("Validate candidate GeoParquet")
        commit_index = self.content.index("Commit validated candidate artifacts")
        self.assertLess(build_index, validation_index)
        self.assertLess(validation_index, commit_index)
        self.assertIn("gpd.read_parquet", self.content)
        self.assertIn("frame.crs.to_epsg() == 4326", self.content)
        self.assertIn("frame.geometry.is_empty.any()", self.content)
        self.assertIn('frame["codigo_comuna"].is_unique', self.content)
        self.assertIn("len(value) == 5 and value.isdigit()", self.content)
        self.assertIn("len(value) == 2 and value.isdigit()", self.content)
        self.assertIn('metadata.get("source_mode") == "live"', self.content)
        self.assertIn("Missing staging CSV", self.content)
        self.assertIn("Missing staging metadata", self.content)
        self.assertIn("Missing raw BCN geometry snapshot", self.content)

    def test_workflow_never_reuses_staging_or_publishes_fallback_data(self):
        self.assertNotIn("--skip-fetch", self.content)
        self.assertIn('metadata.get("source_mode") == "live"', self.content)

    def test_commit_stages_only_allowed_geometry_artifacts_and_checksum(self):
        expected_paths = [
            "data/normalized/geometria_comunal.parquet",
            "data/staging/geometria_comunal.csv",
            "data/staging/geometria_comunal.metadata.json",
            "data/normalized/geometria_comunal.parquet.sha256",
            "data/raw/bcn_geometria_comunal_*.json",
        ]
        for path in expected_paths:
            self.assertIn(path, self.content)
        self.assertIn("sha256sum -c geometria_comunal.parquet.sha256", self.content)
        self.assertIn('git add -f "$path"', self.content)
        self.assertIn("[skip ci]", self.content)

        commit_block = self.content.split("Commit validated candidate artifacts", 1)[1].split(
            "- name: Summary", 1
        )[0]
        staged_paths = [
            line.strip().rstrip("\\").strip()
            for line in commit_block.splitlines()
            if "data/" in line
        ]
        self.assertEqual(staged_paths, expected_paths)

    def test_workflow_does_not_call_stable_pipeline_or_bundle(self):
        self.assertNotIn("make build", self.content)
        self.assertNotIn("make extract", self.content)
        self.assertNotIn("package-bundle", self.content)
        self.assertNotIn("build_dev_db.py", self.content)


def _extract_make_target(makefile_content: str, target_name: str) -> str:
    """Extrae el cuerpo (líneas con tab-indent) de un target de Makefile."""
    lines = makefile_content.splitlines()
    target_prefix = f"{target_name}:"
    body_lines = []
    in_target = False
    for line in lines:
        if line.startswith(target_prefix):
            in_target = True
            continue
        if in_target:
            if line.startswith("\t"):
                body_lines.append(line)
            elif line.strip() == "":
                continue
            else:
                break
    return "\n".join(body_lines)


class HfPublishJobGuardrailTests(unittest.TestCase):
    """Canal de distribución Hugging Face Hub agregado 2026-07 (Plan 059).

    Regresiones a evitar: que el job desaparezca silenciosamente del
    workflow de release, que el script deje de excluir el carril
    `candidate` por construcción, o que otro job pase a depender de
    `hf-publish` convirtiéndolo en bloqueante del release (viola el diseño:
    HF es un canal de descubrimiento best-effort, nunca debe bloquear PyPI
    ni GitHub Releases).
    """

    def test_workflow_has_hf_publish_job_with_token_secret(self):
        content = PYPI_RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("hf-publish:", content)
        self.assertIn("secrets.HF_TOKEN", content)

    def test_publish_script_exists_with_redistribution_and_dry_run(self):
        content = PUBLISH_HF_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("redistribution_ok", content)
        self.assertIn("--dry-run", content)

    def test_workflow_never_names_candidate_lane_datasets(self):
        """El carril candidate se excluye por construcción (ausencia de
        `outputs` en el catálogo) — nunca por una lista hardcodeada en el
        workflow, que podría quedar stale si se agrega un candidate nuevo."""
        content = PYPI_RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("delincuencia_comunal", content)
        self.assertNotIn("autoridades_locales", content)

    def test_hf_publish_is_not_a_blocking_dependency(self):
        """Ningún otro job debe listar hf-publish en su `needs` — es el
        último eslabón de la cadena y su falla no debe afectar a nadie más.

        Cubre tanto `needs: hf-publish` / `needs: [hf-publish]` (inline, en la
        misma línea) como el estilo YAML de lista de bloque:
            needs:
              - hf-publish
        """
        content = PYPI_RELEASE_WORKFLOW.read_text(encoding="utf-8")
        lines = content.splitlines()
        in_needs_block = False
        needs_indent = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("needs:"):
                if "hf-publish" in stripped:
                    self.fail(
                        f"Un job depende de hf-publish, lo que lo volveria bloqueante: {line!r}"
                    )
                # `needs:` sin valor en la misma linea -> puede venir una lista
                # de bloque en las lineas siguientes, mas indentadas.
                in_needs_block = stripped == "needs:"
                needs_indent = len(line) - len(line.lstrip(" "))
                continue
            if in_needs_block:
                current_indent = len(line) - len(line.lstrip(" "))
                if stripped.startswith("-") and current_indent > needs_indent:
                    if "hf-publish" in stripped:
                        self.fail(f"Un job depende de hf-publish (lista de bloque): {line!r}")
                    continue
                in_needs_block = False


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main(sys.argv))
