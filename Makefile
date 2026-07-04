PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
VENV_DIR ?= .venv

.PHONY: help bootstrap install-browsers doctor extract build verify verify-dev verify-readiness verify-publication verify-live verify-landing test coverage lint lint-fix format format-check package package-check package-smoke check refresh status catalog hub-list hub-summary hub-summary-table hub-example hub-artifacts hub-shared-artifacts hub-shared-artifacts-table hub-reports hub-reports-table hub-report hub-inventory hub-inventory-table hub-snapshot hub-snapshot-table hub-overview hub-overview-table hub-status hub-status-table hub-health hub-health-table hub-bundle hub-freshness-audit hub-freshness-audit-table hub-runtime-status hub-runtime-status-table hub-top-issue hub-top-issue-text hub-top-issue-table hub-packages hub-packages-table hub-package hub-package-verify hub-redistribution hub-redistribution-table hub-provenance hub-provenance-table hub-drift hub-drift-table hub-source-readiness hub-dataset-quality package-bundle clean-publishable docs-build docs-serve

help:
	@printf "Targets disponibles:\n"
	@printf "  make bootstrap        Crea .venv e instala dependencias\n"
	@printf "  make install-browsers Instala Chromium para smoke tests de la landing\n"
	@printf "  make doctor           Muestra el Python efectivo y dependencias clave\n"
	@printf "  make extract          Ejecuta extractores\n"
	@printf "  make build            Compila outputs del hub\n"
	@printf "  make verify           Verifica artefactos generados (perfil dev)\n"
	@printf "  make verify-dev       Igual que verify (perfil dev explícito)\n"
	@printf "  make verify-readiness Valida registry, contratos, source_readiness y dataset_quality\n"
	@printf "  make verify-publication Exige datos live y frescos aptos para publicación\n"
	@printf "  make verify-live      [obsoleto] Usa verify-publication en su lugar\n"
	@printf "  make verify-landing   Corre smoke check de la landing en navegador\n"
	@printf "  make test             Corre smoke tests\n"
	@printf "  make coverage         Corre tests con reporte de cobertura\n"
	@printf "  make freshness-badge  Genera el badge de frescura de datos\n"
	@printf "  make coverage-badge   Genera el badge de cobertura desde coverage.xml\n"
	@printf "  make package          Construye wheel + sdist\n"
	@printf "  make package-check    Valida dist/* con twine\n"
	@printf "  make package-smoke    Instala wheel local y prueba import + CLI\n"
	@printf "  make check            Ejecuta build + verify + test + verify-landing\n"
	@printf "  make refresh          Ejecuta extract + build + verify + test + verify-landing + lint + format-check\n"
	@printf "  make status           Imprime resumen humano del pipeline\n"
	@printf "  make catalog          Muestra dataset_catalog.json\n"
	@printf "  make hub-list         Lista datasets via CLI\n"
	@printf "  make hub-summary      Resume datasets via CLI\n"
	@printf "  make hub-summary-table Muestra summary tabular del hub\n"
	@printf "  make hub-example      Muestra ejemplo de uso del dataset comunas\n"
	@printf "  make hub-artifacts    Lista artefactos publicables del dataset comunas\n"
	@printf "  make hub-shared-artifacts Lista artefactos compartidos del hub\n"
	@printf "  make hub-shared-artifacts-table Muestra indice tabular de artefactos compartidos\n"
	@printf "  make hub-reports      Lista reportes compartidos del hub\n"
	@printf "  make hub-reports-table Muestra indice tabular de reportes compartidos\n"
	@printf "  make hub-report       Resuelve metadata del reporte hub_health en JSON\n"
	@printf "  make hub-inventory    Muestra inventario compacto del hub\n"
	@printf "  make hub-inventory-table Muestra inventario tabular del hub\n"
	@printf "  make hub-snapshot     Muestra snapshot humano y compacto del hub\n"
	@printf "  make hub-snapshot-table Muestra snapshot tabular del hub\n"
	@printf "  make hub-overview     Muestra vista agregada compacta del hub\n"
	@printf "  make hub-overview-table Muestra overview tabular del hub\n"
	@printf "  make hub-status       Muestra status operativo compacto del hub\n"
	@printf "  make hub-status-table Muestra status operativo en tabla compacta\n"
	@printf "  make hub-health       Muestra salud agregada del hub\n"
	@printf "  make hub-health-table Muestra salud agregada en tabla compacta\n"
	@printf "  make hub-bundle       Muestra bundle consolidado del hub\n"
	@printf "  make hub-freshness-audit Recalcula frescura actual del hub\n"
	@printf "  make hub-freshness-audit-table Muestra auditoria tabular de frescura actual\n"
	@printf "  make hub-runtime-status Muestra estado runtime agregado del hub\n"
	@printf "  make hub-runtime-status-table Muestra estado runtime en tabla compacta\n"
	@printf "  make hub-top-issue    Muestra la capa prioritaria que requiere atención\n"
	@printf "  make hub-top-issue-text Muestra top issue en formato breve\n"
	@printf "  make hub-top-issue-table Muestra top issue en tabla compacta\n"
	@printf "  make hub-packages     Muestra paquetes publicables del hub\n"
	@printf "  make hub-packages-table Muestra indice tabular de paquetes publicables\n"
	@printf "  make hub-package      Muestra el package principal del hub\n"
	@printf "  make hub-package-verify Muestra metadata de verificacion del package principal\n"
	@printf "  make hub-redistribution Muestra inventario de redistribucion del hub\n"
	@printf "  make hub-redistribution-table Muestra redistribucion en tabla compacta\n"
	@printf "  make hub-provenance   Muestra inventario de procedencia del hub\n"
	@printf "  make hub-provenance-table Muestra procedencia en tabla compacta\n"
	@printf "  make hub-drift        Muestra inventario de drift operativo del hub\n"
	@printf "  make hub-drift-table  Muestra drift en tabla compacta\n"
	@printf "  make hub-source-readiness Muestra madurez de fuente por dataset\n"
	@printf "  make hub-dataset-quality Muestra puntuacion de calidad por dataset\n"
	@printf "  make package-bundle   Genera ZIP publicable desde el manifest\n"
	@printf "  make clean-publishable Elimina artefactos livianos versionables\n"

bootstrap:
	uv sync --extra pipeline --extra dev
	$(PYTHON) -m playwright install chromium
	$(PYTHON) -m pre_commit install

install-browsers:
	$(PYTHON) -m playwright install chromium

doctor:
	@printf "PYTHON=%s\n" "$(PYTHON)"
	@$(PYTHON) -c "import sys; print(sys.executable)"
	@$(PYTHON) -c "import duckdb, polars, pyarrow; from importlib.metadata import version; print('duckdb=' + duckdb.__version__); print('polars=' + polars.__version__); print('pyarrow=' + pyarrow.__version__); print('playwright=' + version('playwright'))"
	@$(PYTHON) scripts/check_validation_registration.py

	PYTHONPATH=src $(PYTHON) src/extractors/subdere_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/bcentral_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/censo_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/censo_hogares_viviendas_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/salud_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/electoral_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/mineduc_establecimientos_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/sinim_finanzas_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/mineduc_resultados_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/siedu_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/res_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/pobreza_extractor.py
	PYTHONPATH=src $(PYTHON) src/extractors/consumo_electrico_extractor.py

build:
	$(PYTHON) src/build_dev_db.py

verify:
	$(PYTHON) scripts/verify_pipeline.py --profile dev

verify-dev:
	$(PYTHON) scripts/verify_pipeline.py --profile dev

verify-readiness:
	$(PYTHON) scripts/verify_pipeline.py --profile readiness

verify-publication:
	$(PYTHON) scripts/verify_pipeline.py --profile publication

verify-live:
	$(PYTHON) scripts/verify_pipeline.py --require-live

verify-landing:
	$(PYTHON) scripts/verify_landing.py

test:
	$(PYTHON) -m pytest

coverage:
	$(PYTHON) -m pytest --cov=src/chile_hub --cov-report=term-missing --cov-report=xml

lint:
	$(PYTHON) -m ruff check src/ tests/ scripts/

lint-fix:
	$(PYTHON) -m ruff check --fix src/ tests/ scripts/

format:
	$(PYTHON) -m ruff format src/ tests/ scripts/

format-check:
	$(PYTHON) -m ruff format --check src/ tests/ scripts/

docs-build:
	$(PYTHON) -m mkdocs build

docs-serve:
	$(PYTHON) -m mkdocs serve

package:
	$(PYTHON) -m build

package-check: package
	$(PYTHON) -m twine check dist/*

package-smoke: package-check
	uv pip install --force-reinstall dist/*.whl
	$(PYTHON) -c "from chile_hub import ChileHub; print(ChileHub)"
	chile-hub --help

check: build verify test verify-landing lint format-check

freshness-badge:
	$(PYTHON) scripts/generate_freshness_badge.py

coverage-badge:
	$(PYTHON) scripts/generate_coverage_badge.py

refresh: extract build verify test verify-landing lint format-check freshness-badge

status:
	$(PYTHON) scripts/pipeline_status.py

catalog:
	@cat data/normalized/dataset_catalog.json

hub-list:
	PYTHONPATH=src $(PYTHON) -m chile_hub list

hub-summary:
	PYTHONPATH=src $(PYTHON) -m chile_hub summary

hub-summary-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub summary --format table

hub-example:
	PYTHONPATH=src $(PYTHON) -m chile_hub example comunas --kind python

hub-artifacts:
	PYTHONPATH=src $(PYTHON) -m chile_hub artifacts comunas

hub-shared-artifacts:
	PYTHONPATH=src $(PYTHON) -m chile_hub shared-artifacts --shared-type hub_health --artifact-format json

hub-shared-artifacts-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub shared-artifacts --shared-type hub_health --artifact-format json --output table

hub-reports:
	PYTHONPATH=src $(PYTHON) -m chile_hub reports

hub-reports-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub reports --format table

hub-report:
	PYTHONPATH=src $(PYTHON) -m chile_hub report hub_health --format json

hub-inventory:
	PYTHONPATH=src $(PYTHON) -m chile_hub inventory

hub-inventory-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub inventory --format table

hub-snapshot:
	PYTHONPATH=src $(PYTHON) -m chile_hub snapshot

hub-snapshot-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub snapshot --format table

hub-overview:
	PYTHONPATH=src $(PYTHON) -m chile_hub overview

hub-overview-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub overview --format table

hub-status:
	PYTHONPATH=src $(PYTHON) -m chile_hub status

hub-status-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub status --format table

hub-health:
	PYTHONPATH=src $(PYTHON) -m chile_hub health

hub-health-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub health --format table

hub-bundle:
	PYTHONPATH=src $(PYTHON) -m chile_hub bundle

hub-freshness-audit:
	PYTHONPATH=src $(PYTHON) -m chile_hub freshness-audit

hub-freshness-audit-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub freshness-audit --format table

hub-runtime-status:
	PYTHONPATH=src $(PYTHON) -m chile_hub runtime-status

hub-runtime-status-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub runtime-status --format table

hub-top-issue:
	PYTHONPATH=src $(PYTHON) -m chile_hub top-issue

hub-top-issue-text:
	PYTHONPATH=src $(PYTHON) -m chile_hub top-issue --format text

hub-top-issue-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub top-issue --format table

hub-packages:
	PYTHONPATH=src $(PYTHON) -m chile_hub packages

hub-packages-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub packages --format table

hub-package:
	PYTHONPATH=src $(PYTHON) -m chile_hub package

hub-package-verify:
	PYTHONPATH=src $(PYTHON) -m chile_hub verify-package

hub-redistribution:
	PYTHONPATH=src $(PYTHON) -m chile_hub redistribution

hub-redistribution-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub redistribution --format table

hub-provenance:
	PYTHONPATH=src $(PYTHON) -m chile_hub provenance

hub-provenance-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub provenance --format table

hub-drift:
	PYTHONPATH=src $(PYTHON) -m chile_hub drift

hub-drift-table:
	PYTHONPATH=src $(PYTHON) -m chile_hub drift --format table

hub-source-readiness:
	PYTHONPATH=src $(PYTHON) -m chile_hub source-readiness

hub-dataset-quality:
	PYTHONPATH=src $(PYTHON) -m chile_hub dataset-quality

package-bundle:
	$(PYTHON) scripts/package_publishable_bundle.py

clean-publishable:
	$(PYTHON) scripts/package_publishable_bundle.py --clean
