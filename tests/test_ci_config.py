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
LANDING_APP = ROOT_DIR / "app.js"
VERIFY_LANDING_SCRIPT = ROOT_DIR / "scripts" / "verify_landing.py"


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

    def test_extractors_belong_to_exactly_one_lane(self):
        """TECHDEBT-06: un extractor no puede correr en dos carriles.

        Los extractores del carril diario viven solo en `make extract`
        (Makefile); los mensuales solo en `monthly-scrape.yml`; el stub SINIM
        y los candidate en ningún job programado. Un extractor en dos carriles
        duplicaría trabajo o sobrescribiría snapshots (el caso SINIM bloqueó el
        publish diario en 2026-06).
        """
        daily = _extract_make_target(MAKEFILE.read_text(encoding="utf-8"), "extract")
        daily_extractors = {
            line.strip()
            for line in daily.splitlines()
            if "extractors/" in line and "_extractor.py" in line
        }
        monthly = MONTHLY_SCRAPE_WORKFLOW.read_text(encoding="utf-8")
        monthly_extractors = {
            f"src/extractors/{name}"
            for name in ("sinim_finanzas_live_extractor.py", "cead_delincuencia_live_extractor.py")
            if f"{name}" in monthly
        }
        overlap = daily_extractors & monthly_extractors
        self.assertEqual(overlap, set(), f"Extractores en dos carriles: {overlap}")
        self.assertNotIn("sinim_finanzas_extractor.py", daily_extractors)

    def test_extraction_lanes_doc_is_referenced_from_agents(self):
        """TECHDEBT-06: la vista de carriles (`docs/extraction-lanes.md`) debe
        seguir referenciada desde AGENTS.md §3 para que el split diario/mensual
        no vuelva a quedar solo en el código."""
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("docs/extraction-lanes.md", agents)


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

    def test_release_falls_back_to_a_publication_grade_artifact(self):
        """El release debe poder adjuntar datos verificados.

        El run que dispara PyPI Release es casi siempre `push`, y esos
        construyen con perfil `readiness`; los artefactos publication-grade
        vienen de `schedule`/`workflow_dispatch`, que rara vez coinciden con
        commits publicables. Sin fallback, la condicion `ready == 'true'` nunca
        se cumple — de hecho ningun release del proyecto llego a tener assets
        adjuntos. El fallback nunca debe relajar el criterio: solo acepta
        `verification_profile == publication` con `require_live`.
        """
        content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("is_publication_grade", content)
        self.assertIn('select(.event=="schedule" or .event=="workflow_dispatch")', content)
        self.assertIn('p.get("verification_profile") == "publication"', content)
        self.assertIn('p.get("require_live") is True', content)
        # Degradacion segura: si no hay artefacto verificado, no se adjunta nada.
        self.assertIn('echo "ready=false" >> "$GITHUB_OUTPUT"', content)

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

    def test_release_downloads_to_staging_and_only_adopts_verified_artifacts(self):
        """El paso pipeline-assets no debe borrar `data/normalized/` del checkout
        antes de validar un artefacto publication-grade.

        Regresion 2026-08-11 (runs 31530278428 y 31532875763): el paso hacia
        `rm -rf data/normalized` al inicio y en cada `try_download`. Cuando no
        existia ningun artefacto publication-grade (caso tipico: el run que
        dispara el release es `push`, perfil `readiness`), el paso terminaba con
        `ready=false` pero con `data/normalized/` vacio; el paso siguiente
        (`sync_release_artifact_version.py`) fallaba con "Missing generated
        artifacts: pipeline_metadata.json, hub_bundle.json, datapackage.json" y
        el release entero moria. Ahora la descarga va a `.pipeline-assets/` y
        solo se copia sobre `data/normalized/` tras validar el artefacto, de
        modo que sin artefacto verificado el release procede usando los
        artefactos commiteados.
        """
        content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        # La descarga nunca adopta sobre data/normalized sin pasar por la validacion.
        self.assertLess(
            content.index("is_publication_grade"),
            content.index("rm -rf data/normalized"),
            "rm -rf data/normalized debe aparecer despues de is_publication_grade",
        )
        # La validacion ocurre sobre el staging, no sobre el checkout.
        self.assertIn('is_publication_grade "$staging_dir"', content)
        self.assertIn('staging_dir=".pipeline-assets/$candidate"', content)
        # Sin artefacto publication-grade, el release continua con los artefactos
        # commiteados (no se aborta): el wipe solo ocurre en la ruta de adopcion.
        self.assertIn('echo "ready=false" >> "$GITHUB_OUTPUT"', content)

    def test_release_installs_pipeline_extra_for_require_live_verification(self):
        """El job release debe instalar el extra `pipeline`, no solo `dev`.

        El paso pipeline-assets corre `verify_pipeline.py --require-live`
        sobre el artefacto descargado; ese script importa `duckdb` vía
        `build_dev_db` → `builders.formats`, y `duckdb` vive en el extra
        `pipeline`. Regresion 2026-08-11 (run 31533777382): el primer release
        que encontró un artefacto publication-grade murió con
        "ModuleNotFoundError: No module named 'duckdb'" en la verificación
        --require-live — con `uv sync --extra dev` a secas, la verificación
        nunca pudo pasar en el entorno del release.
        """
        content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("uv sync --extra dev --extra pipeline", content)
        self.assertNotIn("uv sync --extra dev\n", content)

    def test_release_degrades_to_ready_false_when_recheck_fails(self):
        """La re-verificacion del artefacto no debe matar el release.

        Regresion 2026-08-11 (run 31544671830): el release adopto el unico
        artefacto publication-grade disponible, cuya provenance era de antes
        de que el override se registrara (sin allow_stale_backfills), y la
        re-verificacion rechazo ipc stale — el case abortaba el release
        COMPLETO con exit 1. El diseno correcto (y el del propio workflow en
        ready=false) es degradar: el paquete PyPI se publica igual, solo no se
        adjuntan datos.
        """
        content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        # El fallo se captura con un `if` (no con recheck_status=$?, que bajo
        # set -e moriria antes de asignar — P1 de la review del PR #57).
        self.assertIn("if python scripts/verify_pipeline.py --profile release", content)
        self.assertIn("se publica sin adjuntar datos", content)
        # La degradacion ocurre DENTRO del case 0 (tras la re-verificacion),
        # no en el branch de error (*) que aborta.
        self.assertIn('echo "ready=false" >> "$GITHUB_OUTPUT"', content)

    def test_release_syncs_readme_pin_before_commit(self):
        """El release debe sincronizar el README (pin de version) en el mismo
        commit del bump.

        Regresion 2026-08-12: el release 1.23.1 bumpo pyproject.toml pero no
        toco README.md (no estaba en el git add del release workflow), dejando
        el pin en 1.23.0; el siguiente push a main (merge del PR #58) fallo el
        gate sync_readme_version_pin_example del job quality y cancelo Pages
        Deploy. El commit de release ahora corre `python scripts/sync_docs.py
        --version-only` (fix/write-races: el sync COMPLETO regeneraria bloques
        de datos desde un artifact potencialmente viejo) e incluye README.md
        en el git add — sin data/normalized ni index/app.
        """
        content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("python scripts/sync_docs.py --version-only", content)
        self.assertIn("python scripts/check_landing_sync.py", content)
        self.assertIn(
            "git add CHANGELOG.md pyproject.toml uv.lock README.md index.html app.js", content
        )
        # El commit del release ya NO incluye data/normalized (fix/write-races):
        # la data de main la escribe solo el publish diario. index/app sí van
        # (cache-buster de version).
        self.assertNotIn("data/normalized/ README.md index.html app.js", content)
        self.assertNotIn("uv.lock data/normalized/", content)
        # El sync debe correr ANTES del commit (mismo commit de release).
        landing_sync_index = content.index("python scripts/check_landing_sync.py")
        sync_index = content.index("python scripts/sync_docs.py")
        commit_index = content.index('git commit -m "chore(release)')
        self.assertLess(landing_sync_index, commit_index)
        self.assertLess(sync_index, commit_index)

    def test_hf_publish_uses_the_adopted_publication_grade_run(self):
        """hf-publish debe bajar el run que release efectivamente adopto.

        En la ruta fallback, el artefacto publication-grade viene de
        `assets_run_id` (un run schedule/dispatch), no del run que disparo el
        release (`run_id`, casi siempre push/readiness). Si hf-publish bajara
        `run_id`, publicaria en HF el artefacto no verificado del push.
        """
        content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("assets_run_id: ${{ steps.pipeline-assets.outputs.assets_run_id }}", content)
        self.assertIn('run_id="${{ needs.release.outputs.assets_run_id }}"', content)
        self.assertIn('if [[ -z "$run_id" ]]; then', content)

    def test_release_replays_stale_backfill_override_from_provenance(self):
        """El release debe re-verificar el artefacto con el mismo override con
        el que se publico.

        Regresion 2026-08-11: el pipeline publico el artefacto con
        `--allow-stale-backfills ipc` (issue #43), pero el release re-corria
        `verify_pipeline.py --require-live` sin ese override, con lo que el
        gate de ADR-016 rechazaba un artefacto ya verificado. La provenance
        debe registrar el override y el release debe releerlo y pasarlo.
        """
        pipeline_content = (ROOT_DIR / ".github" / "workflows" / "pipeline-check.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '"allow_stale_backfills": "${{ inputs.allow_stale_backfills }}"',
            pipeline_content,
        )
        release_content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('p.get("allow_stale_backfills", "")', release_content)
        self.assertIn("--allow-stale-backfills", release_content)
        self.assertIn("python scripts/verify_pipeline.py --profile release", release_content)

    def test_release_verifies_with_release_profile_not_require_live(self):
        """El release debe re-verificar con el perfil `release`, no con
        `--require-live` (perfil publication).

        Regresion 2026-08-11 (run 31539295351): `--require-live` exige
        `data/staging/*.csv` (gitignored, 298 MB, no viaja en el artefacto),
        asi que la re-verificacion fallaba con "Missing required files:
        data/staging/..." en TODO release. El perfil `release` verifica la
        publication policy sobre lo que viaja (normalized) sin staging.
        """
        release_content = (ROOT_DIR / ".github" / "workflows" / "pypi-release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("--profile release", release_content)
        # La invocacion real de verify_pipeline en el release no puede usar
        # --require-live (perfil publication, exige staging). Los comentarios
        # pueden mencionarlo al documentar la regresion — se filtra la primera
        # columna de comando (lineas sin `#`).
        command_lines = [
            line
            for line in release_content.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertFalse(
            any("verify_pipeline.py --require-live" in line for line in command_lines),
            "verify_pipeline.py --require-live no debe invocarse en el release",
        )
        verify_content = (ROOT_DIR / "scripts" / "verify_pipeline.py").read_text(encoding="utf-8")
        self.assertIn('if profile == "release":', verify_content)
        self.assertIn('choices=["dev", "readiness", "publication", "release"]', verify_content)

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

    def test_package_version_badge_uses_the_versioned_app_asset(self):
        """El bundle de datos puede llegar después que una release de paquete.

        En 1.28.7, ``hub_bundle.json`` seguía en 1.28.4 y app.js sobrescribió
        el badge de la navbar con ese valor. El cache-buster de app.js se
        sincroniza desde pyproject.toml en cada release, por lo que es la fuente
        correcta para la versión del paquete que el sitio anuncia.
        """
        app_content = LANDING_APP.read_text(encoding="utf-8")
        verification_content = VERIFY_LANDING_SCRIPT.read_text(encoding="utf-8")

        self.assertIn(
            "packageVersionBadge.textContent = `v${CHILE_HUB_ASSET_VERSION}`;",
            app_content,
        )
        self.assertNotIn('versionBadge.textContent = "v" + bundle.version;', app_content)
        self.assertIn("expected_version = project_version", verification_content)

    def test_health_table_escapes_status_values_in_class_attributes(self):
        """SEC-03: los valores de estado del dashboard de salud deben escaparse
        también en los atributos `class`, no solo en el texto.

        `hub_health.json` es generado por el pipeline (valores enum internos),
        pero la tabla de salud es la unica superficie donde un valor externo
        (p. ej. un severity malformado) se interpolaba crudo en `class=` — un
        vector de attribute injection. Los seis estados (severity, source_mode,
        validation_status, freshness_status, coverage_status, drift_status)
        deben pasar por escapeHtml antes de entrar a la clase.
        """
        content = (ROOT_DIR / "app.js").read_text(encoding="utf-8")
        for var, status in (
            ("sev", "severity"),
            ("sourceMode", "source_mode"),
            ("validationStatus", "validation_status"),
            ("freshnessStatus", "freshness_status"),
            ("coverageStatus", "coverage_status"),
            ("driftStatus", "drift_status"),
        ):
            with self.subTest(status=status):
                self.assertIn(f"const {var} = escapeHtml(entry.{status}", content)
                self.assertIn(f"class=\"pill ' + {var}", content)


class DocsSyncGateGuardrailTests(unittest.TestCase):
    """El gate de sync de docs debe auto-corregirse en push a main (carrera
    con releases) pero seguir bloqueante en PRs.

    Regresion 2026-08-12 (x2): semantic-release publico 1.23.1, 1.24.0 y
    1.24.1 en menos de una hora; el release pushea el bump de version entre
    la creacion de un PR y su merge, dejando el pin del README con la version
    anterior. El CI del merge fallaba con "sync_readme_version_pin_example"
    pese a que el PR no tenia regresion — un drift operativamente inevitable.
    """

    def test_quality_job_runs_docs_sync_gate(self):
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python scripts/sync_docs.py --check", content)

    def test_pipeline_workflow_listens_to_merge_group(self):
        """El workflow de Pipeline Check debe escuchar el evento merge_group.

        Requisito de la merge queue de GitHub: la cola crea ramas temporales
        gh-readonly-queue/main/... y dispara el evento merge_group; sin este
        trigger, los checks requeridos nunca se reportan y la cola falla todos
        los merges. Sin esto, habilitar "Require merge queue" en la branch
        protection romperia todos los merges futuros.
        """
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("merge_group:", content)
        # La cola no debe cancelar builds en curso (prueba varios PRs en paralelo).
        cancel_line = [line for line in content.splitlines() if "cancel-in-progress:" in line][0]
        self.assertNotIn("merge_group", cancel_line)

    def test_required_codeql_check_listens_to_merge_group(self):
        """CodeQL es un check requerido de la rama: debe escuchar merge_group.

        P1 de la review del PR #61: con CodeQL en los checks requeridos pero
        sin el trigger merge_group en codeql.yml, cada merge en cola esperaria
        un check que nunca se reporta y la cola se bloquearia para siempre.
        """
        codeql = (ROOT_DIR / ".github" / "workflows" / "codeql.yml").read_text(encoding="utf-8")
        self.assertIn("merge_group:", codeql)

    def test_docs_auto_heal_lives_in_separate_main_only_job(self):
        """El auto-heal debe vivir en un job separado (docs-autosync),
        condicionado a push a main, NUNCA en el job quality (que debe
        permanecer read-only).

        P1 de la review del PR #60: dar contents: write al job quality
        permitiria que un PR de una rama del repo ejecute codigo controlado
        por el PR con un token de escritura. El job separado corre el codigo
        de main (push aprobado), nunca el de una rama de PR.
        """
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        # El job separado existe y esta condicionado a push a main.
        self.assertIn("  docs-autosync:", content)
        self.assertIn("name: Auto-sync docs (push a main)", content)
        self.assertIn(
            "if: github.event_name == 'push' && github.ref == 'refs/heads/main' && always()",
            content,
        )
        # El commit del bot usa GITHUB_TOKEN (no dispara workflows push -> sin loop).
        self.assertIn("git push origin HEAD:main", content)
        self.assertIn('git commit -m "docs: auto-sync tras carrera con release [skip ci]"', content)
        # El gate del job quality es el check puro (read-only): el bloque entre
        # el header del job quality y el comentario del job docs-autosync no
        # debe contener un bloque de permissions propio.
        quality_section = content.split("  quality:")[1].split("  # Auto-heal de docs")[0]
        self.assertIn("python scripts/sync_docs.py --check", quality_section)
        self.assertNotIn("permissions:", quality_section)

    def test_docs_gate_still_blocking_on_pr(self):
        """En PRs el gate sigue exigiendo el sync del autor (quality falla)."""
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python scripts/sync_docs.py --check", content)
        # El auto-heal nunca corre en PRs (job condicionado a push a main).
        self.assertIn(
            "if: github.event_name == 'push' && github.ref == 'refs/heads/main' && always()",
            content,
        )


class AgentsSyncGateGuardrailTests(unittest.TestCase):
    """AGENTS.md es prosa curada: sus hechos contables (anclas de líneas,
    listas de módulos del §2, tabla de capas del §1) no se regeneran con
    `sync_docs.py` y por eso stale (conteos de líneas y módulos desactualizados
    detectados 2026-08). `check_agents_sync.py` los verifica contra el código;
    estos guardrails evitan que el gate se desconecte del job rápido o de
    `make doctor`."""

    def test_quality_job_runs_agents_sync_gate(self):
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python scripts/check_agents_sync.py", content)

    def test_doctor_target_runs_agents_sync_gate(self):
        body = _extract_make_target(MAKEFILE.read_text(encoding="utf-8"), "doctor")
        self.assertIn(
            "scripts/check_agents_sync.py",
            body,
            "`make doctor` debe correr el gate de AGENTS.md antes de commit.",
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

    def test_publish_script_filters_by_publication_track_from_registry(self):
        """El script HF debe filtrar por `publication_track` del registry, no
        inferir el carril de `outputs` del catálogo.

        Plan 070: la asunción "candidate nunca declara outputs" era falsa —
        perfil_territorial_comunal y consumo_electrico_comunal (candidate,
        el segundo deprecated) tienen outputs y llegaron al mirror HF como
        si fueran publicables. El registry es la fuente de verdad del carril.
        """
        content = PUBLISH_HF_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("SOURCE_REGISTRY_PATH", content)
        self.assertIn("publication_track", content)
        self.assertIn('track != "stable_publishable"', content)

    def test_publish_script_dry_run_excludes_candidate_and_deprecated(self):
        """El dry-run debe listar 18 capas (no 19): candidate/deprecated fuera.

        Regresión del Plan 070: con el catálogo real, consumo (candidate/
        deprecated) no debe aparecer en la lista de parquets del mirror.
        perfil_territorial_comunal SÍ debe aparecer desde el Plan 084
        (promovido a stable_publishable 2026-08-12).
        """
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(PUBLISH_HF_SCRIPT), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
            env={**__import__("os").environ, "HF_TOKEN": "x"},
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("data/regiones.parquet", result.stdout)
        self.assertIn("data/perfil_territorial_comunal.parquet", result.stdout)
        self.assertNotIn("data/consumo_electrico_comunal.parquet", result.stdout)

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


class LandingCandidateLaneGuardrailTests(unittest.TestCase):
    """Plan 082: la landing debe exponer el carril candidate sin contaminar
    el catálogo estable.

    Antes de este plan, hub_bundle.json producía candidate_datasets que
    ninguna UI consumía — perfil_territorial_comunal (346/346, validation
    ok) era invisible en la superficie principal. Si una futura refactor de
    app.js eliminara el render candidate o el contador del buscador volviera
    a contar candidate cards, los consumidores del sitio perderían la única
    señal visual de qué datasets NO están en el bundle público.
    """

    def _app_js(self):
        return (ROOT_DIR / "app.js").read_text(encoding="utf-8")

    def test_app_js_renders_candidate_section_from_bundle(self):
        content = self._app_js()
        self.assertIn("renderCandidateSection", content)
        self.assertIn("bundle.candidate_datasets", content)
        self.assertIn('section.id = "cat-candidate"', content)
        self.assertIn('class="dataset-badge candidate"', content)
        self.assertIn("candidate-next-action", content)
        self.assertIn('href="data/normalized/hub_bundle.json"', content)

    def test_search_count_excludes_candidate_cards(self):
        content = self._app_js()
        self.assertIn('.dataset-card:not(.candidate-card)")', content)
        self.assertIn("stableVisibleCount", content)
        self.assertIn("catalogCount.textContent = `", content)
        no_result = "if (visibleCount === 0 && cards.length > 0)"
        self.assertIn(no_result, content)

    def test_verify_landing_checks_candidate_section(self):
        content = (ROOT_DIR / "scripts" / "verify_landing.py").read_text(encoding="utf-8")
        self.assertIn("#cat-candidate", content)
        self.assertIn("candidate_datasets", content)
        self.assertIn(".candidate-card", content)
        self.assertIn('"0 capas"', content)


class BotWriteRaceGuardrailTests(unittest.TestCase):
    """Regresión 2026-08-13 (fix/write-races): tres carreras encadenadas
    sobre main por escritores de bot:

    R1. El release 1.28.2/1.28.3 bajaba el artifact del pipeline MÁS
        RECIENTE EXITOSO (posiblemente de un commit anterior al último
        merge) y lo commitaba a main junto con README/index.html/app.js
        regenerados desde esa data vieja — pisando data fresca y el README
        del Plan 084 (94.2 vs 95.2), rompiendo los gates de todos los PRs
        siguientes.
    R2. El publish diario NO commitaba README.md, así que el bloque de
        health/quality regenerado quedaba desincronizado en main hasta el
        siguiente push (gap que dejó el README en 94.2 tras el release).
    R3. Los bots escribían main sin serialización: dos pull --rebase
        concurrentes podían colisionar sin retry.

    Solución: el release solo versiona (nunca data), el publish commitea
    README, y todos los bots comparten el grupo de concurrency
    `bot-writes-main`.
    """

    def test_release_never_commits_data_or_derived_assets(self):
        content = PYPI_RELEASE_WORKFLOW.read_text(encoding="utf-8")
        # El commit del release NO debe incluir data/normalized: los datos
        # de main los escribe solo el publish diario. El release SÍ usa
        # data/normalized para adjuntar assets al GitHub Release y para
        # hf-publish — eso no es commitear a main, y el guard no debe
        # confundirlo. index.html/app.js SÍ van en el commit (cache-buster
        # de version regenerado por sync_release_artifact_version.py, P1 de
        # la review del PR #77).
        commit_block = content.split("git commit -m")[0].split("git add")[-1]
        self.assertNotIn("data/normalized", commit_block)
        self.assertIn("index.html", commit_block)
        self.assertIn("app.js", commit_block)

    def test_release_uses_version_only_sync_docs(self):
        content = PYPI_RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("sync_docs.py --version-only", content)
        # No debe correr el sync completo (regeneraría bloques de data desde
        # el artifact potencialmente viejo).
        self.assertNotIn("python scripts/sync_docs.py\n", content)

    def test_publish_commits_readme(self):
        content = PIPELINE_CHECK_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("git add --all data/normalized/ index.html app.js README.md", content)

    def test_all_bot_writers_share_concurrency_group(self):
        for path in (
            PIPELINE_CHECK_WORKFLOW,
            PYPI_RELEASE_WORKFLOW,
            MONTHLY_SCRAPE_WORKFLOW,
            GEOMETRIA_COMUNAL_WORKFLOW,
            ADOPTION_STATS_WORKFLOW,
        ):
            content = path.read_text(encoding="utf-8")
            self.assertIn(
                "group: bot-writes-main", content, f"{path.name} sin grupo de concurrency"
            )
            self.assertIn("cancel-in-progress: false", content, f"{path.name} con cancel permitido")

    def test_sync_docs_version_only_flag_exists(self):
        content = (ROOT_DIR / "scripts" / "sync_docs.py").read_text(encoding="utf-8")
        self.assertIn("--version-only", content)
        self.assertIn("sync_readme_version_pin_example", content)


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main(sys.argv))
