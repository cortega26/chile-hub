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
MAKEFILE = ROOT_DIR / "Makefile"
MKDOCS_CONFIG = ROOT_DIR / "mkdocs.yml"
DOCS_DIR = ROOT_DIR / "docs"


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


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main(sys.argv))
