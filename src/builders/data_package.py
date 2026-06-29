"""Generacion del descriptor Frictionless Data Package (datapackage.json).

Capa de PUBLICACION derivada de los contratos internos (contracts/datasets/*.schema.json)
y del dataset_catalog.json. NO reemplaza el formato interno (ver ADR-005); solo
expone el hub en un estandar interoperable del ecosistema open-data.
"""

import os
from datetime import datetime

from src.builders._shared import NORMALIZED_DIR, UTC
from src.builders.io_utils import write_json_atomic
from src.builders.metadata import load_schema_contract

# chile-hub column_types -> Frictionless Table Schema types
_TYPE_MAP = {
    "string": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
    "date": "date",
}


def _build_fields(dataset_name, catalog_fields):
    """Construye los fields de Table Schema a partir del contrato + fields del catalogo."""
    contract = load_schema_contract(dataset_name) or {}
    column_types = contract.get("column_types", {})
    required = set(contract.get("required_columns", []))
    fields = []
    for column in catalog_fields:
        ftype = _TYPE_MAP.get(column_types.get(column, "string"), "string")
        field = {"name": column, "type": ftype}
        if column in required:
            field["constraints"] = {"required": True}
        fields.append(field)
    return fields, contract.get("primary_key", [])


def build_data_package(dataset_catalog, version, homepage):
    """Construye el dict del Frictionless Data Package desde el catalogo."""
    resources = []
    for entry in dataset_catalog.get("datasets", []):
        name = entry["dataset"]
        outputs = entry.get("outputs", {})
        parquet_path = outputs.get("parquet")
        if not parquet_path:
            continue  # solo datasets con Parquet publicado
        fields, primary_key = _build_fields(name, entry.get("fields", []))
        reuse = entry.get("reuse_policy", {}) or {}
        schema = {"fields": fields, "missingValues": [""]}
        if primary_key:
            schema["primaryKey"] = primary_key
        resource = {
            "name": name,
            "path": os.path.basename(parquet_path),
            "format": "parquet",
            "mediatype": "application/vnd.apache.parquet",
            "title": name,
            "description": entry.get("description", ""),
            "schema": schema,
        }
        if entry.get("source_name") or entry.get("source_url"):
            resource["sources"] = [
                {"title": entry.get("source_name", ""), "path": entry.get("source_url", "")}
            ]
        if reuse.get("license") or reuse.get("license_url"):
            resource["licenses"] = [
                {"title": reuse.get("license", ""), "path": reuse.get("license_url", "")}
            ]
        resources.append(resource)

    return {
        "name": "chile-hub",
        "title": "chile-hub -- Datos publicos de Chile curados",
        "description": (
            "Capa de datos reproducible y curada sobre datasets publicos oficiales "
            "de Chile: geografia, demografia, salud, educacion, finanzas municipales "
            "e indicadores."
        ),
        "version": version,
        "homepage": homepage,
        "created": datetime.now(UTC).isoformat(),
        "resources": resources,
    }


def write_data_package_json(dataset_catalog, version, homepage):
    """Genera y escribe data/normalized/datapackage.json. Retorna la ruta."""
    package = build_data_package(dataset_catalog, version, homepage)
    output_path = os.path.join(NORMALIZED_DIR, "datapackage.json")
    write_json_atomic(package, output_path, ensure_ascii=False, indent=2)
    return output_path
