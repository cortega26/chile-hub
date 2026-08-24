"""Phase 2 — tests de equivalencia del piloto DatasetSpec (partidos_politicos).

Cada aserción es una garantía de equivalencia mecánica (ADR-018/019): la
proyección del spec debe ser idéntica a la entrada legacy correspondiente, y
el overlay shadow no puede alterar ningún resultado público. Convenciones de
comparación del Phase 1: equivalencia semántica estricta, sin allowlists
inesperadas y con fallos visibles.

No requiere ``data/normalized/``: el build offline se ejecuta bajo un
directorio temporal (mismo patrón que ``test_phase1_characterization.py``).
"""

from __future__ import annotations

import json
from csv import DictWriter
from dataclasses import asdict
from pathlib import Path

import pytest

from chile_hub.datasets import Dataset
from src import build_dev_db, validation
from src.builders._shared import DATASET_CATALOG_CONFIG
from src.registry.dataset_spec import (
    CONTRACT_OWNED_KEYS,
    DatasetSpecError,
    catalog_config_with_spec_overlay,
    has_spec,
    iter_specs,
    load_dataset_spec,
    parse_dataset_spec,
    source_registry_with_spec_overlay,
)
from tests.test_phase1_characterization import _isolated_main_paths

ROOT_DIR = Path(__file__).resolve().parents[1]
PILOT = "partidos_politicos"


def _legacy_catalog() -> dict:
    return json.loads(
        (ROOT_DIR / "data" / "dataset_catalog_config.json").read_text(encoding="utf-8")
    )


def _legacy_registry() -> list[dict]:
    return json.loads((ROOT_DIR / "data" / "source_registry.json").read_text(encoding="utf-8"))


def _legacy_registry_entry() -> dict:
    for entry in _legacy_registry():
        if entry["dataset"] == PILOT:
            return entry
    raise AssertionError(f"{PILOT} ausente de data/source_registry.json")


def _contract_payload() -> dict:
    return json.loads(
        (ROOT_DIR / "contracts" / "datasets" / f"{PILOT}.schema.json").read_text(encoding="utf-8")
    )


def _spec() -> object:
    return load_dataset_spec(PILOT)


class TestPilotSpecModel:
    def test_pilot_spec_loads_with_typed_fields(self) -> None:
        spec = _spec()
        assert spec.dataset == PILOT
        assert spec.kind == "direct"
        assert spec.alias_for is None
        assert spec.dependencies == ()
        assert spec.publication_track == "stable_publishable"
        assert spec.public_bundle_eligible is True
        assert spec.extraction_lane == "bajo_demanda"
        assert spec.extractor == "src/extractors/partidos_politicos_extractor.py"
        assert spec.validator == "validate_partidos_politicos"
        assert hasattr(validation, spec.validator)
        assert (ROOT_DIR / spec.contract_path).is_file()

    def test_only_one_spec_exists(self) -> None:
        # Phase 2: solo pilot; Phase 3A: 10 specs; Phase 3B: 13 specs; Phase 3C: 15 specs
        specs = list(iter_specs())
        assert _spec() in specs
        assert len(specs) == 15
        assert {s.dataset for s in specs} == {
            "partidos_politicos",
            "censo_comunal",
            "censo_hogares_viviendas",
            "distritos_electorales",
            "empresas",
            "establecimientos_educacionales",
            "establecimientos_salud",
            "indicadores_urbanos_siedu",
            "pobreza_comunal",
            "resultados_educacionales",
            "regiones",
            "provincias",
            "comunas",
            "comunas_enriquecidas",
            "perfil_territorial_comunal",
        }

    def test_spec_declares_no_structural_schema_facts(self) -> None:
        for spec_path in (ROOT_DIR / "data" / "dataset_specs").glob("*.json"):
            payload = json.loads(spec_path.read_text(encoding="utf-8"))
            assert not (CONTRACT_OWNED_KEYS & set(payload)), (
                f"{spec_path.name} redacta hechos del contrato"
            )


class TestCatalogProjection:
    def test_catalog_entry_equals_legacy(self) -> None:
        """Garantía B04: la proyección del spec replica exactamente la entrada
        legacy del catálogo para el piloto."""
        assert _spec().to_catalog_entry() == _legacy_catalog()[PILOT]

    def test_all_specs_catalog_entries_equal_legacy(self) -> None:
        """Phase 3A: cada spec del cohort proyecta exactamente su entrada legacy."""
        cat = _legacy_catalog()
        for spec in iter_specs():
            assert spec.to_catalog_entry() == cat[spec.dataset], f"mismatch {spec.dataset}"

    def test_expected_record_count_is_projected_from_contract(self) -> None:
        """P0-D2: expected_record_count es hecho del contrato; el spec no lo
        redacta y la proyección lo lee mecánicamente desde el contrato."""
        spec = _spec()
        contract = _contract_payload()
        entry = spec.to_catalog_entry(contract_payload=contract)
        assert entry["expected_record_count"] == contract["expected_record_count"]
        assert entry["expected_record_count"] == _legacy_catalog()[PILOT]["expected_record_count"]

    def test_contract_reference_is_stable_and_resolvable(self) -> None:
        for spec in iter_specs():
            assert spec.contract_reference() == {"path": spec.contract_path}
            assert (ROOT_DIR / spec.contract_path).is_file()

    def test_documentation_metadata_equals_legacy(self) -> None:
        legacy = _legacy_catalog()[PILOT]
        projected = _spec().documentation_metadata()
        assert projected["description"] == legacy["description"]
        assert projected["usage_examples"] == legacy["usage_examples"]
        assert projected["path"] == legacy["documentation"]

    def test_artifact_declarations_equal_legacy_outputs(self) -> None:
        cat = _legacy_catalog()
        for spec in iter_specs():
            assert spec.artifact_declarations() == cat[spec.dataset]["outputs"]


class TestSourceRegistryProjection:
    def test_source_registry_entry_equals_legacy(self) -> None:
        """Garantía B12: la proyección del spec replica exactamente la entrada
        legacy del registry de fuentes para el piloto."""
        assert _spec().to_source_registry_entry() == _legacy_registry_entry()

    def test_all_specs_source_registry_entries_equal_legacy(self) -> None:
        reg = {e["dataset"]: e for e in _legacy_registry()}
        for spec in iter_specs():
            assert spec.to_source_registry_entry() == reg[spec.dataset], f"mismatch {spec.dataset}"


class TestPublicInventoryPolicy:
    def test_pilot_public_eligibility_matches_enum_membership(self) -> None:
        """Política Phase 2 (documentada en docs/architecture-migration-phase-2-pilot.md):
        stable_publishable + public_bundle_eligible ⇒ miembro del enum público."""
        inventory = _spec().public_inventory()
        assert inventory["public"] is True
        assert inventory["track"] == "stable_publishable"
        assert Dataset.PARTIDOS_POLITICOS.value == PILOT
        assert PILOT in Dataset.values()

    def test_enum_surface_is_unchanged(self) -> None:
        assert [member.value for member in Dataset] == [
            "regiones",
            "provincias",
            "comunas",
            "comunas_enriquecidas",
            "indicadores",
            "censo_comunal",
            "censo_hogares_viviendas",
            "establecimientos_salud",
            "establecimientos_educacionales",
            "distritos_electorales",
            "partidos_politicos",
            "autoridades_electas",
            "finanzas_municipales",
            "resultados_educacionales",
            "indicadores_urbanos_siedu",
            "pobreza_comunal",
            "consumo_electrico_comunal",
            "empresas",
            "perfil_territorial_comunal",
        ]


class TestOverlayAdapters:
    def test_catalog_overlay_keeps_non_pilot_entries_untouched(self) -> None:
        legacy = _legacy_catalog()
        overlaid = catalog_config_with_spec_overlay(legacy)
        assert set(overlaid) == set(legacy)
        specs = {s.dataset: s for s in iter_specs()}
        for dataset_id, entry in legacy.items():
            if dataset_id in specs:
                assert overlaid[dataset_id] == specs[dataset_id].to_catalog_entry()
            else:
                assert overlaid[dataset_id] == entry

    def test_registry_overlay_keeps_non_pilot_entries_untouched(self) -> None:
        legacy = _legacy_registry()
        overlaid = source_registry_with_spec_overlay(legacy)
        assert len(overlaid) == len(legacy)
        specs = {s.dataset: s for s in iter_specs()}
        for legacy_entry, overlaid_entry in zip(legacy, overlaid):
            ds = legacy_entry["dataset"]
            if ds in specs:
                assert overlaid_entry == specs[ds].to_source_registry_entry()
            else:
                assert overlaid_entry == legacy_entry

    def test_overlay_is_semantically_identical_to_legacy(self) -> None:
        """Garantía más fuerte: con la proyección igual a la entrada legacy,
        el catálogo/registry completos son idénticos — ningún consumidor del
        build puede ver una diferencia."""
        assert catalog_config_with_spec_overlay(_legacy_catalog()) == _legacy_catalog()
        assert source_registry_with_spec_overlay(_legacy_registry()) == _legacy_registry()

    def test_runtime_catalog_config_flows_through_spec_projection(self) -> None:
        """El módulo cargado por el build (import-time) ya trae el overlay:
        su entrada del piloto debe coincidir con la proyección del spec."""
        specs = {s.dataset: s for s in iter_specs()}
        for ds, spec in specs.items():
            assert DATASET_CATALOG_CONFIG[ds] == spec.to_catalog_entry()


class TestFailClosed:
    def test_missing_spec_fails_closed(self) -> None:
        assert has_spec("dataset_inexistente") is False
        with pytest.raises(DatasetSpecError, match="No existe DatasetSpec"):
            load_dataset_spec("dataset_inexistente")

    def test_spec_rejects_contract_owned_facts(self) -> None:
        payload = json.loads(
            (ROOT_DIR / "data" / "dataset_specs" / f"{PILOT}.json").read_text(encoding="utf-8")
        )
        payload["columns"] = [{"name": "id_partido", "type": "string"}]
        with pytest.raises(DatasetSpecError, match="contrato JSON Schema"):
            parse_dataset_spec(payload, source_path=f"{PILOT}.json")

    def test_spec_fails_closed_on_missing_operational_field(self) -> None:
        payload = json.loads(
            (ROOT_DIR / "data" / "dataset_specs" / f"{PILOT}.json").read_text(encoding="utf-8")
        )
        del payload["publication_track"]
        with pytest.raises(DatasetSpecError, match="faltan claves"):
            parse_dataset_spec(payload, source_path=f"{PILOT}.json")

    def test_spec_fails_closed_on_unknown_kind(self) -> None:
        payload = json.loads(
            (ROOT_DIR / "data" / "dataset_specs" / f"{PILOT}.json").read_text(encoding="utf-8")
        )
        payload["kind"] = "fantasma"
        with pytest.raises(DatasetSpecError, match="kind"):
            parse_dataset_spec(payload, source_path=f"{PILOT}.json")

    def test_direct_kind_rejects_alias_for(self) -> None:
        payload = json.loads(
            (ROOT_DIR / "data" / "dataset_specs" / f"{PILOT}.json").read_text(encoding="utf-8")
        )
        payload["alias_for"] = "comunas"
        with pytest.raises(DatasetSpecError, match="direct"):
            parse_dataset_spec(payload, source_path=f"{PILOT}.json")

    def test_spec_fails_closed_on_unresolvable_contract(self) -> None:
        payload = json.loads(
            (ROOT_DIR / "data" / "dataset_specs" / f"{PILOT}.json").read_text(encoding="utf-8")
        )
        payload["contract_path"] = "contracts/datasets/inexistente.schema.json"
        with pytest.raises(DatasetSpecError, match="contrato referenciado"):
            parse_dataset_spec(payload, source_path=f"{PILOT}.json")


def _write_partidos_staging(staging: Path) -> None:
    """Escribe el staging sintético del piloto (36 filas, cobertura completa)."""
    rows = []
    for number in range(1, 37):
        sigla = f"P{number:02d}"
        rows.append(
            {
                "id_partido": sigla,
                "nombre": f"Partido Sintetico {number:02d}",
                "sigla": sigla,
                "estado_legal": "constituido" if number <= 15 else "",
                "fecha_constitucion": "1988-05-02" if number <= 15 else "",
                "ambito": "",
                "fuente": "Cámara de Diputadas y Diputados",
                "url_fuente": "https://opendata.camara.cl/",
                "fecha_consulta": "2026-08-23",
            }
        )
    with (staging / "partidos_politicos.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (staging / "partidos_politicos.metadata.json").write_text(
        json.dumps(
            {
                "dataset": PILOT,
                "source_name": "Phase 2 static fixture",
                "source_url": "https://example.invalid/phase-2-fixture",
                "source_mode": "live",
                "source_detail": "static_test_literal",
                "refreshed_at_utc": "2026-08-23T12:00:00+00:00",
                "record_count": len(rows),
                "fields": list(rows[0]),
                "notes": [],
                "reuse_policy": {
                    "status": "open-attribution",
                    "license": "CC-BY",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "attribution_required": True,
                    "redistribution_ok": True,
                    "summary": "Deterministic test fixture only.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


class TestSpecBackedBuild:
    def test_pilot_build_reads_through_spec_backed_path(self, tmp_path: Path) -> None:
        """Garantía P0-D4: un build offline completo con staging del piloto,
        ejecutado sobre el catálogo/registry ya proyectados, emite los mismos
        hechos que la proyección del spec y los artefactos públicos del piloto."""
        with _isolated_main_paths(tmp_path) as stack:
            staging = stack.sandbox / "data" / "staging"  # type: ignore[attr-defined]
            _write_partidos_staging(staging)
            build_dev_db.main()
            normalized = stack.sandbox / "data" / "normalized"  # type: ignore[attr-defined]

        spec = _spec()
        pipeline_metadata = json.loads(
            (normalized / "pipeline_metadata.json").read_text(encoding="utf-8")
        )
        catalog = json.loads((normalized / "dataset_catalog.json").read_text(encoding="utf-8"))
        manifest = json.loads((normalized / "artifact_manifest.json").read_text(encoding="utf-8"))
        source_readiness = json.loads(
            (normalized / "source_readiness.json").read_text(encoding="utf-8")
        )

        pilot_metadata = pipeline_metadata["datasets"][PILOT]
        pilot_catalog = next(entry for entry in catalog["datasets"] if entry["dataset"] == PILOT)

        # Hechos operacionales del spec fluyen al metadata y al catálogo público.
        assert pilot_metadata["reuse_policy"] == asdict(spec.reuse_policy)
        assert pilot_metadata["freshness"]["status"] == "fresh"
        assert pilot_metadata["freshness"]["max_age_hours"] == spec.freshness_policy.max_age_hours
        assert pilot_catalog["description"] == spec.documentation.description
        assert pilot_catalog["join_keys"] == list(spec.join_keys)
        assert pilot_catalog["confidence_tier"] == spec.confidence_tier
        assert pilot_catalog["outputs"] == spec.outputs
        assert pilot_catalog["documentation"] == spec.documentation.path
        assert pilot_catalog["usage_examples"] == spec.documentation.usage_examples

        # Política de fuente del spec fluye al source readiness.
        readiness = next(
            entry for entry in source_readiness["datasets"] if entry["dataset"] == PILOT
        )
        assert readiness["source_id"] == spec.source.source_id
        assert readiness["official_url"] == spec.source.official_url
        assert readiness["maturity_status"] == spec.maturity_status
        assert readiness["license_status"] == spec.source.license_status

        # Artefactos públicos declarados por el spec se emiten y entran al
        # manifiesto (carril stable, bundle-eligible — B04).
        for output_path in spec.outputs.values():
            assert (ROOT_DIR / output_path).is_file() or (
                normalized.parent.parent / output_path
            ).is_file()
        manifest_paths = {entry["path"] for entry in manifest["artifacts"]}
        assert "data/normalized/partidos_politicos.parquet" in manifest_paths
        assert "data/normalized/partidos_politicos.json" in manifest_paths

        # La validación semántica referenciada por el spec corre y pasa.
        assert pipeline_metadata["validations"][PILOT]["status"] == "ok"
