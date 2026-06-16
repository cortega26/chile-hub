PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
VENV_DIR ?= .venv

.PHONY: help bootstrap install-browsers doctor extract build verify verify-live verify-landing test lint lint-fix format format-check check refresh status catalog hub-list hub-summary hub-summary-table hub-example hub-artifacts hub-shared-artifacts hub-shared-artifacts-table hub-reports hub-reports-table hub-report hub-inventory hub-inventory-table hub-snapshot hub-snapshot-table hub-overview hub-overview-table hub-status hub-status-table hub-health hub-health-table hub-bundle hub-freshness-audit hub-freshness-audit-table hub-runtime-status hub-runtime-status-table hub-top-issue hub-top-issue-text hub-top-issue-table hub-packages hub-packages-table hub-package hub-package-verify hub-redistribution hub-redistribution-table hub-provenance hub-provenance-table hub-drift hub-drift-table package-bundle clean-publishable

help:
	@printf "Targets disponibles:\n"
	@printf "  make bootstrap        Crea .venv e instala dependencias\n"
	@printf "  make install-browsers Instala Chromium para smoke tests de la landing\n"
	@printf "  make doctor           Muestra el Python efectivo y dependencias clave\n"
	@printf "  make extract          Ejecuta extractores\n"
	@printf "  make build            Compila outputs del hub\n"
	@printf "  make verify           Verifica artefactos generados\n"
	@printf "  make verify-live      Exige datos live y frescos aptos para publicación\n"
	@printf "  make verify-landing   Corre smoke check de la landing en navegador\n"
	@printf "  make test             Corre smoke tests\n"
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
	@printf "  make package-bundle   Genera ZIP publicable desde el manifest\n"
	@printf "  make clean-publishable Elimina artefactos livianos versionables\n"

bootstrap:
	@python3 -c "import sys; v=sys.version_info; ok=v>=(3,13); sys.exit(0 if ok else f'Python 3.13+ requerido, se encontró {v.major}.{v.minor}')"
	python3 -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/python -m pip install --upgrade pip
	$(VENV_DIR)/bin/python -m pip install -r requirements.txt
	$(VENV_DIR)/bin/python -m pip install -r dev-requirements.txt
	$(VENV_DIR)/bin/python -m playwright install chromium
	$(VENV_DIR)/bin/python -m pre_commit install

install-browsers:
	$(PYTHON) -m playwright install chromium

doctor:
	@printf "PYTHON=%s\n" "$(PYTHON)"
	@$(PYTHON) -c "import sys; print(sys.executable)"
	@$(PYTHON) -c "import duckdb, polars; from importlib.metadata import version; print('duckdb=' + duckdb.__version__); print('polars=' + polars.__version__); print('playwright=' + version('playwright'))"

extract:
	$(PYTHON) src/extractors/subdere_extractor.py
	$(PYTHON) src/extractors/bcentral_extractor.py
	$(PYTHON) src/extractors/censo_extractor.py
	$(PYTHON) src/extractors/censo_hogares_viviendas_extractor.py
	$(PYTHON) src/extractors/salud_extractor.py
	$(PYTHON) src/extractors/electoral_extractor.py
	$(PYTHON) src/extractors/mineduc_establecimientos_extractor.py

build:
	$(PYTHON) src/build_dev_db.py

verify:
	$(PYTHON) scripts/verify_pipeline.py

verify-live:
	$(PYTHON) scripts/verify_pipeline.py --require-live

verify-landing:
	$(PYTHON) scripts/verify_landing.py

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src/ tests/ scripts/

lint-fix:
	$(PYTHON) -m ruff check --fix src/ tests/ scripts/

format:
	$(PYTHON) -m ruff format src/ tests/ scripts/

format-check:
	$(PYTHON) -m ruff format --check src/ tests/ scripts/

check: build verify test verify-landing lint format-check

refresh: extract build verify test verify-landing lint format-check

status:
	$(PYTHON) scripts/pipeline_status.py

catalog:
	@cat data/normalized/dataset_catalog.json

hub-list:
	$(PYTHON) -m src.chile_hub list

hub-summary:
	$(PYTHON) -m src.chile_hub summary

hub-summary-table:
	$(PYTHON) -m src.chile_hub summary --format table

hub-example:
	$(PYTHON) -m src.chile_hub example comunas --kind python

hub-artifacts:
	$(PYTHON) -m src.chile_hub artifacts comunas

hub-shared-artifacts:
	$(PYTHON) -m src.chile_hub shared-artifacts --shared-type hub_health --artifact-format json

hub-shared-artifacts-table:
	$(PYTHON) -m src.chile_hub shared-artifacts --shared-type hub_health --artifact-format json --output table

hub-reports:
	$(PYTHON) -m src.chile_hub reports

hub-reports-table:
	$(PYTHON) -m src.chile_hub reports --format table

hub-report:
	$(PYTHON) -m src.chile_hub report hub_health --format json

hub-inventory:
	$(PYTHON) -m src.chile_hub inventory

hub-inventory-table:
	$(PYTHON) -m src.chile_hub inventory --format table

hub-snapshot:
	$(PYTHON) -m src.chile_hub snapshot

hub-snapshot-table:
	$(PYTHON) -m src.chile_hub snapshot --format table

hub-overview:
	$(PYTHON) -m src.chile_hub overview

hub-overview-table:
	$(PYTHON) -m src.chile_hub overview --format table

hub-status:
	$(PYTHON) -m src.chile_hub status

hub-status-table:
	$(PYTHON) -m src.chile_hub status --format table

hub-health:
	$(PYTHON) -m src.chile_hub health

hub-health-table:
	$(PYTHON) -m src.chile_hub health --format table

hub-bundle:
	$(PYTHON) -m src.chile_hub bundle

hub-freshness-audit:
	$(PYTHON) -m src.chile_hub freshness-audit

hub-freshness-audit-table:
	$(PYTHON) -m src.chile_hub freshness-audit --format table

hub-runtime-status:
	$(PYTHON) -m src.chile_hub runtime-status

hub-runtime-status-table:
	$(PYTHON) -m src.chile_hub runtime-status --format table

hub-top-issue:
	$(PYTHON) -m src.chile_hub top-issue

hub-top-issue-text:
	$(PYTHON) -m src.chile_hub top-issue --format text

hub-top-issue-table:
	$(PYTHON) -m src.chile_hub top-issue --format table

hub-packages:
	$(PYTHON) -m src.chile_hub packages

hub-packages-table:
	$(PYTHON) -m src.chile_hub packages --format table

hub-package:
	$(PYTHON) -m src.chile_hub package

hub-package-verify:
	$(PYTHON) -m src.chile_hub verify-package

hub-redistribution:
	$(PYTHON) -m src.chile_hub redistribution

hub-redistribution-table:
	$(PYTHON) -m src.chile_hub redistribution --format table

hub-provenance:
	$(PYTHON) -m src.chile_hub provenance

hub-provenance-table:
	$(PYTHON) -m src.chile_hub provenance --format table

hub-drift:
	$(PYTHON) -m src.chile_hub drift

hub-drift-table:
	$(PYTHON) -m src.chile_hub drift --format table

package-bundle:
	$(PYTHON) scripts/package_publishable_bundle.py

clean-publishable:
	$(PYTHON) scripts/package_publishable_bundle.py --clean
