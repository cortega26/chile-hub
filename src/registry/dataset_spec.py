"""DatasetSpec tipado — modelo declarativo operacional por dataset (Phase 2).

Autoridad (ADR-018): ``DatasetSpec`` posee identidad, ciclo de vida, carril
de publicación y elegibilidad pública, política de fuente/reúso/fallback/
frescura, carril de extracción, referencia al contrato, referencia al
validador semántico, aliases, dependencias, outputs declarados y metadatos de
documentación. Los contratos JSON Schema siguen siendo la autoridad separada
para campos, tipos, nulabilidad, restricciones estructurales y compatibilidad
de esquema; este módulo rechaza explícitamente que un spec redacte esos
hechos.

El piloto Phase 2 (``partidos_politicos``) se lee a través de este modelo en
los lectores de build mediante proyecciones mecánicas; todo dataset sin spec
sigue leyéndose íntegramente de las configuraciones legacy. Las funciones
``*_with_spec_overlay`` implementan ese adapter/shadow: si no hay specs
presentes devuelven la configuración legacy sin cambios.

Este módulo es stdlib-only y no importa código del proyecto, igual que
``src/builders/doc_sync.py``.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from typing import Any, Iterator, Mapping

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPECS_DIR = os.path.join(ROOT_DIR, "data", "dataset_specs")

SPEC_FORMAT_VERSION = "1.0"

# Hechos que pertenecen al contrato JSON Schema (ADR-018/ADR-005): campos,
# tipos, nulabilidad, claves, cobertura estructural y outputs de publicación
# del esquema. Un spec que los redacte es un error de autoridad, no una
# extensión; ver `_REJECTED_SPEC_KEYS`.
CONTRACT_OWNED_KEYS = frozenset(
    {
        "columns",
        "column_types",
        "nullable_columns",
        "required_columns",
        "primary_key",
        "expected_record_count",
        "coverage_policy",
        "publish_outputs",
    }
)

VALID_KINDS = frozenset({"direct", "alias", "derived"})
VALID_PUBLICATION_TRACKS = frozenset({"stable_publishable", "candidate"})
VALID_MATURITY_STATUSES = frozenset({"stable", "candidate", "experimental", "deprecated"})

_REQUIRED_SPEC_KEYS = frozenset(
    {
        "spec_version",
        "dataset",
        "kind",
        "publication_track",
        "public_bundle_eligible",
        "maturity_status",
        "confidence_tier",
        "extraction_lane",
        "extractor",
        "contract_path",
        "validator",
        "alias_for",
        "dependencies",
        "source",
        "reuse_policy",
        "freshness_policy",
        "documentation",
        "outputs",
        "join_keys",
    }
)

_SOURCE_REQUIRED_KEYS = frozenset(
    {
        "source_id",
        "source_name",
        "official_url",
        "access_method",
        "license_status",
        "live_extractor_status",
        "fallback_policy",
        "live_ready",
        "fallback_allowed",
        "publish_blocking",
        "review_by",
        "stalled_after_days",
        "owner",
        "next_action",
    }
)

_REUSE_REQUIRED_KEYS = frozenset(
    {
        "status",
        "license",
        "license_url",
        "attribution_required",
        "redistribution_ok",
        "summary",
    }
)

_FRESHNESS_REQUIRED_KEYS = frozenset({"max_age_hours", "label"})

_DOCUMENTATION_REQUIRED_KEYS = frozenset({"description", "path", "usage_examples"})


class DatasetSpecError(Exception):
    """Spec ausente, malformado o con hechos fuera de su autoridad."""


@dataclass(frozen=True)
class SourcePolicy:
    """Política de fuente/fallback del dataset (proyección al source registry)."""

    source_id: str
    source_name: str
    official_url: str
    access_method: str
    license_status: str
    live_extractor_status: str
    fallback_policy: str
    live_ready: bool
    fallback_allowed: bool
    publish_blocking: bool
    review_by: str | None
    stalled_after_days: int
    owner: str
    next_action: str
    source_notes: str | None = None


@dataclass(frozen=True)
class ReusePolicy:
    """Política legal de reúso declarada por el dataset."""

    status: str
    license: str
    license_url: str
    attribution_required: bool
    redistribution_ok: bool
    summary: str


@dataclass(frozen=True)
class FreshnessPolicy:
    """Política de frescura del dataset."""

    max_age_hours: int
    label: str


@dataclass(frozen=True)
class DocumentationMetadata:
    """Metadatos de documentación del dataset."""

    description: str
    path: str
    usage_examples: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetSpec:
    """Declaración operacional tipada de un dataset.

    No contiene hechos de esquema: el contrato referenciado por
    ``contract_path`` es la autoridad separada (ADR-018).
    """

    spec_version: str
    dataset: str
    kind: str
    publication_track: str
    public_bundle_eligible: bool
    maturity_status: str
    confidence_tier: str
    extraction_lane: str
    extractor: str | None
    contract_path: str
    validator: str
    alias_for: str | None
    dependencies: tuple[str, ...]
    source: SourcePolicy
    reuse_policy: ReusePolicy
    freshness_policy: FreshnessPolicy
    documentation: DocumentationMetadata
    outputs: dict[str, str]
    join_keys: tuple[str, ...]
    catalog_notes: str | None = None

    # -- Proyecciones de compatibilidad (mecánicas, no fuentes duplicadas) --

    def contract_reference(self) -> dict[str, str]:
        """Referencia estable al contrato JSON Schema (ADR-018, P0-D2)."""
        return {"path": self.contract_path}

    def documentation_metadata(self) -> dict[str, object]:
        """Metadatos de documentación proyectables al catálogo legacy."""
        return {
            "path": self.documentation.path,
            "description": self.documentation.description,
            "usage_examples": dict(self.documentation.usage_examples),
        }

    def artifact_declarations(self) -> dict[str, str]:
        """Outputs físicos declarados por el dataset."""
        return dict(self.outputs)

    def public_inventory(self) -> dict[str, object]:
        """Elegibilidad pública e inventario del enum ``Dataset``.

        Política Phase 2: un dataset ``stable_publishable`` y
        ``public_bundle_eligible`` pertenece al enum público ``Dataset``;
        los candidatos pueden o no estar (la superficie actual no cambia).
        """
        public = (
            self.publication_track == "stable_publishable" and self.public_bundle_eligible is True
        )
        return {
            "dataset": self.dataset,
            "public": public,
            "track": self.publication_track,
            "bundle_eligible": self.public_bundle_eligible,
        }

    def to_catalog_entry(self, contract_payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Proyección del spec a la forma exacta de la entrada legacy del catálogo.

        ``expected_record_count`` no se redacta aquí: se proyecta
        mecánicamente desde el contrato referenciado (autoridad de esquema).
        """
        payload = contract_payload if contract_payload is not None else _load_contract(self)
        entry: dict[str, Any] = {
            "description": self.documentation.description,
            "join_keys": list(self.join_keys),
            "confidence_tier": self.confidence_tier,
            "extractor": self.extractor,
        }
        if payload is not None and "expected_record_count" in payload:
            entry["expected_record_count"] = payload["expected_record_count"]
        entry.update(
            {
                "reuse_policy": asdict(self.reuse_policy),
                "freshness_policy": asdict(self.freshness_policy),
                "usage_examples": dict(self.documentation.usage_examples),
                "outputs": dict(self.outputs),
                "documentation": self.documentation.path,
            }
        )
        if self.catalog_notes is not None:
            entry["_notes"] = self.catalog_notes
        if self.kind == "alias":
            entry["alias_for"] = self.alias_for
        return entry

    def to_source_registry_entry(self) -> dict[str, Any]:
        """Proyección del spec a la forma exacta de la entrada legacy del registry."""
        entry: dict[str, Any] = {
            "source_id": self.source.source_id,
            "dataset": self.dataset,
            "source_name": self.source.source_name,
            "official_url": self.source.official_url,
            "access_method": self.source.access_method,
            "license_status": self.source.license_status,
            "live_extractor_status": self.source.live_extractor_status,
            "fallback_policy": self.source.fallback_policy,
            "maturity_status": self.maturity_status,
            "live_ready": self.source.live_ready,
            "fallback_allowed": self.source.fallback_allowed,
            "publish_blocking": self.source.publish_blocking,
            "review_by": self.source.review_by,
            "stalled_after_days": self.source.stalled_after_days,
            "owner": self.source.owner,
            "next_action": self.source.next_action,
            "publication_track": self.publication_track,
            "public_bundle_eligible": self.public_bundle_eligible,
            "cadencia": self.extraction_lane,
        }
        if self.source.source_notes is not None:
            entry["source_notes"] = self.source.source_notes
        return entry


# ---------------------------------------------------------------------------
# Loader fail-closed
# ---------------------------------------------------------------------------


def _require_keys(payload: Mapping[str, Any], required: frozenset[str], where: str) -> None:
    missing = sorted(required - set(payload))
    if missing:
        raise DatasetSpecError(f"DatasetSpec {where}: faltan claves: {', '.join(missing)}")


def _require_str(payload: Mapping[str, Any], key: str, where: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise DatasetSpecError(f"DatasetSpec {where}: '{key}' debe ser string")
    return value


def _require_bool(payload: Mapping[str, Any], key: str, where: str) -> bool:
    value = payload[key]
    if not isinstance(value, bool):
        raise DatasetSpecError(f"DatasetSpec {where}: '{key}' debe ser boolean")
    return value


def _require_int(payload: Mapping[str, Any], key: str, where: str) -> int:
    value = payload[key]
    if not isinstance(value, int) or isinstance(value, bool):
        raise DatasetSpecError(f"DatasetSpec {where}: '{key}' debe ser int")
    return value


def _require_str_list(payload: Mapping[str, Any], key: str, where: str) -> tuple[str, ...]:
    value = payload[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise DatasetSpecError(f"DatasetSpec {where}: '{key}' debe ser lista de strings")
    return tuple(value)


def _require_str_dict(payload: Mapping[str, Any], key: str, where: str) -> dict[str, str]:
    value = payload[key]
    if not isinstance(value, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in value.items()
    ):
        raise DatasetSpecError(f"DatasetSpec {where}: '{key}' debe ser dict de strings")
    return dict(value)


def _parse_source(payload: Mapping[str, Any], where: str) -> SourcePolicy:
    source = payload["source"]
    if not isinstance(source, dict):
        raise DatasetSpecError(f"DatasetSpec {where}: 'source' debe ser objeto")
    _require_keys(source, _SOURCE_REQUIRED_KEYS, f"{where}.source")
    source_notes = source.get("source_notes")
    if source_notes is not None and not isinstance(source_notes, str):
        raise DatasetSpecError(f"DatasetSpec {where}: 'source.source_notes' debe ser string")
    return SourcePolicy(
        source_id=_require_str(source, "source_id", where),
        source_name=_require_str(source, "source_name", where),
        official_url=_require_str(source, "official_url", where),
        access_method=_require_str(source, "access_method", where),
        license_status=_require_str(source, "license_status", where),
        live_extractor_status=_require_str(source, "live_extractor_status", where),
        fallback_policy=_require_str(source, "fallback_policy", where),
        live_ready=_require_bool(source, "live_ready", where),
        fallback_allowed=_require_bool(source, "fallback_allowed", where),
        publish_blocking=_require_bool(source, "publish_blocking", where),
        review_by=source.get("review_by"),
        stalled_after_days=_require_int(source, "stalled_after_days", where),
        owner=_require_str(source, "owner", where),
        next_action=_require_str(source, "next_action", where),
        source_notes=source_notes,
    )


def _parse_reuse(payload: Mapping[str, Any], where: str) -> ReusePolicy:
    reuse = payload["reuse_policy"]
    if not isinstance(reuse, dict):
        raise DatasetSpecError(f"DatasetSpec {where}: 'reuse_policy' debe ser objeto")
    _require_keys(reuse, _REUSE_REQUIRED_KEYS, f"{where}.reuse_policy")
    return ReusePolicy(
        status=_require_str(reuse, "status", where),
        license=_require_str(reuse, "license", where),
        license_url=_require_str(reuse, "license_url", where),
        attribution_required=_require_bool(reuse, "attribution_required", where),
        redistribution_ok=_require_bool(reuse, "redistribution_ok", where),
        summary=_require_str(reuse, "summary", where),
    )


def _parse_freshness(payload: Mapping[str, Any], where: str) -> FreshnessPolicy:
    freshness = payload["freshness_policy"]
    if not isinstance(freshness, dict):
        raise DatasetSpecError(f"DatasetSpec {where}: 'freshness_policy' debe ser objeto")
    _require_keys(freshness, _FRESHNESS_REQUIRED_KEYS, f"{where}.freshness_policy")
    return FreshnessPolicy(
        max_age_hours=_require_int(freshness, "max_age_hours", where),
        label=_require_str(freshness, "label", where),
    )


def _parse_documentation(payload: Mapping[str, Any], where: str) -> DocumentationMetadata:
    documentation = payload["documentation"]
    if not isinstance(documentation, dict):
        raise DatasetSpecError(f"DatasetSpec {where}: 'documentation' debe ser objeto")
    _require_keys(documentation, _DOCUMENTATION_REQUIRED_KEYS, f"{where}.documentation")
    return DocumentationMetadata(
        description=_require_str(documentation, "description", where),
        path=_require_str(documentation, "path", where),
        usage_examples=_require_str_dict(documentation, "usage_examples", where),
    )


def parse_dataset_spec(payload: Mapping[str, Any], *, source_path: str = "<memory>") -> DatasetSpec:
    """Valida y tipa un payload de DatasetSpec; falla cerrado ante cualquier
    violación de forma, tipo o autoridad."""
    where = os.path.basename(source_path)
    if not isinstance(payload, dict):
        raise DatasetSpecError(f"DatasetSpec {where}: el spec debe ser un objeto JSON")

    rejected = sorted(CONTRACT_OWNED_KEYS & set(payload))
    if rejected:
        raise DatasetSpecError(
            f"DatasetSpec {where}: redacta hechos del contrato JSON Schema "
            f"(autoridad de ADR-018): {', '.join(rejected)}. El contrato es la "
            f"fuente de esquema; el spec solo la referencia."
        )
    _require_keys(payload, _REQUIRED_SPEC_KEYS, where)

    spec_version = _require_str(payload, "spec_version", where)
    dataset = _require_str(payload, "dataset", where)
    kind = _require_str(payload, "kind", where)
    if kind not in VALID_KINDS:
        raise DatasetSpecError(
            f"DatasetSpec {where}: 'kind' inválido '{kind}' (válidos: {', '.join(sorted(VALID_KINDS))})"
        )

    publication_track = _require_str(payload, "publication_track", where)
    if publication_track not in VALID_PUBLICATION_TRACKS:
        raise DatasetSpecError(
            f"DatasetSpec {where}: 'publication_track' inválido '{publication_track}'"
        )
    maturity_status = _require_str(payload, "maturity_status", where)
    if maturity_status not in VALID_MATURITY_STATUSES:
        raise DatasetSpecError(
            f"DatasetSpec {where}: 'maturity_status' inválido '{maturity_status}'"
        )

    alias_for = payload.get("alias_for")
    dependencies = _require_str_list(payload, "dependencies", where)
    if kind == "direct":
        if alias_for is not None:
            raise DatasetSpecError(f"DatasetSpec {where}: 'direct' no puede tener alias_for")
        if dependencies:
            raise DatasetSpecError(f"DatasetSpec {where}: 'direct' no puede tener dependencies")
    elif kind == "alias":
        if not isinstance(alias_for, str) or not alias_for:
            raise DatasetSpecError(f"DatasetSpec {where}: 'alias' requiere alias_for")
        if dependencies:
            raise DatasetSpecError(f"DatasetSpec {where}: 'alias' no puede tener dependencies")
    else:  # derived
        if alias_for is not None:
            raise DatasetSpecError(f"DatasetSpec {where}: 'derived' no puede tener alias_for")
        if not dependencies:
            raise DatasetSpecError(f"DatasetSpec {where}: 'derived' requiere dependencies")

    extractor = payload.get("extractor")
    if extractor is not None and not isinstance(extractor, str):
        raise DatasetSpecError(f"DatasetSpec {where}: 'extractor' debe ser string o null")
    if kind != "derived" and not extractor:
        raise DatasetSpecError(
            f"DatasetSpec {where}: 'extractor' es obligatorio para kind '{kind}'"
        )

    contract_path = _require_str(payload, "contract_path", where)
    contract_abs = os.path.join(ROOT_DIR, contract_path)
    if not os.path.isfile(contract_abs):
        raise DatasetSpecError(
            f"DatasetSpec {where}: el contrato referenciado no existe: {contract_path}"
        )

    validator = _require_str(payload, "validator", where)

    catalog_notes = payload.get("catalog_notes")
    if catalog_notes is None:
        catalog_notes = payload.get("_notes")
    if catalog_notes is not None and not isinstance(catalog_notes, str):
        raise DatasetSpecError(f"DatasetSpec {where}: 'catalog_notes' debe ser string")

    return DatasetSpec(
        spec_version=spec_version,
        dataset=dataset,
        kind=kind,
        publication_track=publication_track,
        public_bundle_eligible=_require_bool(payload, "public_bundle_eligible", where),
        maturity_status=maturity_status,
        confidence_tier=_require_str(payload, "confidence_tier", where),
        extraction_lane=_require_str(payload, "extraction_lane", where),
        extractor=extractor,
        contract_path=contract_path,
        validator=validator,
        alias_for=alias_for,
        dependencies=dependencies,
        source=_parse_source(payload, where),
        reuse_policy=_parse_reuse(payload, where),
        freshness_policy=_parse_freshness(payload, where),
        documentation=_parse_documentation(payload, where),
        outputs=_require_str_dict(payload, "outputs", where),
        join_keys=_require_str_list(payload, "join_keys", where),
        catalog_notes=catalog_notes,
    )


def spec_path(dataset_id: str) -> str:
    """Ruta esperada del spec de ``dataset_id`` (no verifica existencia)."""
    return os.path.join(SPECS_DIR, f"{dataset_id}.json")


def has_spec(dataset_id: str) -> bool:
    """¿Existe un archivo de spec para ``dataset_id``?"""
    return os.path.isfile(spec_path(dataset_id))


def load_dataset_spec(dataset_id: str) -> DatasetSpec:
    """Carga y valida el spec de ``dataset_id``; falla cerrado si no existe."""
    path = spec_path(dataset_id)
    if not os.path.isfile(path):
        raise DatasetSpecError(f"No existe DatasetSpec para '{dataset_id}' en {SPECS_DIR}")
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    spec = parse_dataset_spec(payload, source_path=path)
    if spec.dataset != dataset_id:
        raise DatasetSpecError(
            f"DatasetSpec {os.path.basename(path)}: 'dataset' ('{spec.dataset}') "
            f"no coincide con el nombre del archivo ('{dataset_id}')"
        )
    return spec


def iter_specs() -> Iterator[DatasetSpec]:
    """Itera los specs presentes en ``SPECS_DIR`` (vacío si el directorio no existe)."""
    if not os.path.isdir(SPECS_DIR):
        return
    for name in sorted(os.listdir(SPECS_DIR)):
        if name.endswith(".json"):
            yield load_dataset_spec(name[: -len(".json")])


@lru_cache(maxsize=None)
def _load_contract_payload(contract_path: str) -> dict[str, Any] | None:
    """Lee el contrato referenciado (autoridad de esquema) para proyecciones."""
    contract_abs = os.path.join(ROOT_DIR, contract_path)
    try:
        with open(contract_abs, "r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except FileNotFoundError:
        return None


def _load_contract(spec: DatasetSpec) -> dict[str, Any] | None:
    return _load_contract_payload(spec.contract_path)


# ---------------------------------------------------------------------------
# Adapters/shadow sobre las configuraciones legacy
# ---------------------------------------------------------------------------


def catalog_config_with_spec_overlay(legacy: Mapping[str, Any]) -> dict[str, Any]:
    """Catálogo legacy con la entrada de cada dataset con spec reemplazada por
    su proyección. Todo dataset sin spec conserva su entrada legacy intacta.
    Falla cerrado si un spec existe para un dataset ausente del catálogo."""
    result = dict(legacy)
    for spec in iter_specs():
        if spec.dataset not in result:
            raise DatasetSpecError(
                f"DatasetSpec '{spec.dataset}' no está en dataset_catalog_config.json"
            )
        result[spec.dataset] = spec.to_catalog_entry()
    return result


def source_registry_with_spec_overlay(legacy: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Registry de fuentes legacy con la entrada de cada dataset con spec
    reemplazada por su proyección. El resto conserva su entrada intacta."""
    if not os.path.isdir(SPECS_DIR):
        return [dict(entry) for entry in legacy]
    specs = {spec.dataset: spec for spec in iter_specs()}
    result = [dict(entry) for entry in legacy]
    for i, entry in enumerate(result):
        dataset_id = entry.get("dataset")
        spec = specs.get(str(dataset_id)) if isinstance(dataset_id, str) else None
        if spec is not None:
            result[i] = spec.to_source_registry_entry()
    return result
