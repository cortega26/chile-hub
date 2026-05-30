PYTHON ?= python

.PHONY: help extract build verify test check status catalog hub-list hub-summary clean-publishable

help:
	@printf "Targets disponibles:\n"
	@printf "  make extract          Ejecuta extractores\n"
	@printf "  make build            Compila outputs del hub\n"
	@printf "  make verify           Verifica artefactos generados\n"
	@printf "  make test             Corre smoke tests\n"
	@printf "  make check            Ejecuta build + verify + test\n"
	@printf "  make status           Imprime resumen humano del pipeline\n"
	@printf "  make catalog          Muestra dataset_catalog.json\n"
	@printf "  make hub-list         Lista datasets via CLI\n"
	@printf "  make hub-summary      Resume datasets via CLI\n"
	@printf "  make clean-publishable Elimina artefactos livianos versionables\n"

extract:
	$(PYTHON) src/extractors/subdere_extractor.py
	$(PYTHON) src/extractors/bcentral_extractor.py

build:
	$(PYTHON) src/build_dev_db.py

verify:
	$(PYTHON) scripts/verify_pipeline.py

test:
	$(PYTHON) -m unittest discover -s tests

check: build verify test

status:
	$(PYTHON) scripts/pipeline_status.py

catalog:
	@cat data/normalized/dataset_catalog.json

hub-list:
	$(PYTHON) -m src.chile_hub list

hub-summary:
	$(PYTHON) -m src.chile_hub summary

clean-publishable:
	rm -f data/normalized/*.json data/normalized/*.md data/normalized/*.parquet
