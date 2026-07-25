"""Guardrails de configuración de CI/Make que no son expresables como tests de
Python puro, pero cuya regresión ya causó fallos reales de pipeline.

No parsean el YAML con un parser dedicado (evita depender de un paquete
transitivo como pyyaml que no es dependencia directa del proyecto); usan
comprobaciones de texto simples y suficientes para el guardrail específico.
"""

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PIPELINE_CHECK_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "pipeline-check.yml"
MONTHLY_SCRAPE_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "monthly-scrape.yml"
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
