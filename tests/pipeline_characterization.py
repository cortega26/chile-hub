"""Deterministic comparison helpers for Phase 1 migration characterization.

These helpers deliberately live under ``tests``: they describe the current
product boundary and must not become a second production artifact pipeline.
JSON paths in ``volatile_json_paths`` are the *only* tolerated differences;
callers must name each path rather than discard an entire generated file.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Callable, Iterable, Mapping
from csv import DictWriter
from pathlib import Path


def _without_json_paths(
    value: object, paths: set[tuple[str, ...]], prefix: tuple[str, ...] = ()
) -> object:
    """Return ``value`` with precisely allowlisted JSON object paths omitted."""
    if isinstance(value, dict):
        return {
            key: _without_json_paths(item, paths, (*prefix, str(key)))
            for key, item in value.items()
            if (*prefix, str(key)) not in paths
        }
    if isinstance(value, list):
        return [
            _without_json_paths(item, paths, (*prefix, str(index)))
            for index, item in enumerate(value)
        ]
    return value


def artifact_tree_fingerprints(
    root: Path, *, volatile_json_paths: Iterable[tuple[str, ...]] = ()
) -> dict[str, str]:
    """Fingerprint an artifact tree without hiding non-allowlisted differences.

    ``volatile_json_paths`` applies only to JSON object keys (for example,
    ``("generated_at_utc",)``). Binary files and all non-JSON files are hashed
    byte-for-byte, including ZIPs and Parquet files.
    """
    paths = set(volatile_json_paths)
    result: dict[str, str] = {}
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        payload = path.read_bytes()
        if path.suffix == ".json":
            decoded = json.loads(payload)
            payload = json.dumps(
                _without_json_paths(decoded, paths),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        result[relative] = hashlib.sha256(payload).hexdigest()
    return result


def assert_artifact_trees_equivalent(
    left: Path, right: Path, *, volatile_json_paths: Iterable[tuple[str, ...]] = ()
) -> None:
    """Fail with a useful diff when two fixed-input artifact trees differ."""
    left_fingerprints = artifact_tree_fingerprints(left, volatile_json_paths=volatile_json_paths)
    right_fingerprints = artifact_tree_fingerprints(right, volatile_json_paths=volatile_json_paths)
    if left_fingerprints == right_fingerprints:
        return
    paths = sorted(set(left_fingerprints) | set(right_fingerprints))
    differences = [
        path for path in paths if left_fingerprints.get(path) != right_fingerprints.get(path)
    ]
    raise AssertionError(
        "Artifact trees differ outside the explicit volatile allowlist: " + ", ".join(differences)
    )


def _semantic_bytes(path: Path, json_paths: Iterable[tuple[str, ...]]) -> bytes:
    payload = path.read_bytes()
    if path.suffix != ".json":
        return payload
    return json.dumps(
        _without_json_paths(json.loads(payload), set(json_paths)),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def assert_semantic_zip_equivalent(
    left: Path,
    right: Path,
    *,
    volatile_json_paths: dict[str, Iterable[tuple[str, ...]]],
    json_normalizers: Mapping[str, Callable[[object], object]] | None = None,
) -> None:
    """Compare ZIP payloads semantically, never their container timestamps.

    JSON allowlists and optional normalizers are keyed by ZIP member name;
    every binary member is compared byte-for-byte. A normalizer is appropriate
    only when a generated JSON file carries checksums of JSON serialization
    whose object-key order is explicitly non-contractual; callers must still
    verify every checksum against its own produced bytes.
    """
    with zipfile.ZipFile(left) as left_zip, zipfile.ZipFile(right) as right_zip:
        left_members = set(left_zip.namelist())
        right_members = set(right_zip.namelist())
        if left_members != right_members:
            raise AssertionError(f"ZIP member mismatch: {left_members ^ right_members}")
        differences = []
        for member in sorted(left_members):
            suffix = Path(member).suffix
            left_payload = left_zip.read(member)
            right_payload = right_zip.read(member)
            if suffix == ".json":
                allowed = set(volatile_json_paths.get(member, ()))
                left_value = _without_json_paths(json.loads(left_payload), allowed)
                right_value = _without_json_paths(json.loads(right_payload), allowed)
                normalizer = (json_normalizers or {}).get(member)
                if normalizer is not None:
                    left_value = normalizer(left_value)
                    right_value = normalizer(right_value)
                left_payload = json.dumps(
                    left_value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
                right_payload = json.dumps(
                    right_value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            if left_payload != right_payload:
                differences.append(member)
        if differences:
            raise AssertionError("ZIP payload differs: " + ", ".join(differences))


def write_legacy_build_staging_fixture(destination: Path, *, include_candidate: bool) -> None:
    """Write a complete deterministic staging tree for the legacy build.

    The fixture is generated solely from the static literals in this function,
    rather than copied from ``data/staging``.  The legacy validators require
    346 CUT rows for several national datasets, so spelling every row out as a
    committed CSV would add noise without adding meaning.  The formulas below
    make that cardinality, fixed-width CUT preservation, and every value used
    by the validators explicit and reviewable.
    """
    destination.mkdir(parents=True, exist_ok=True)
    commune_rows = [
        {
            "codigo_region": "01",
            "nombre_region": "Region Uno",
            "abreviatura": "RU",
            "codigo_provincia": "011",
            "nombre_provincia": "Provincia Uno",
            "codigo_comuna": f"01{number:03d}",
            "nombre_comuna": f"Comuna {number:03d}",
            "nombre_comuna_clean": f"comuna {number:03d}",
            "latitud_cabecera": "-20.0",
            "longitud_cabecera": "-70.0",
            "poblacion_estimada": "1000",
        }
        for number in range(1, 347)
    ]

    def write_csv(name: str, rows: list[dict[str, object]]) -> None:
        assert rows, f"synthetic fixture {name} must not be empty"
        with (destination / f"{name}.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def write_metadata(
        name: str, rows: list[dict[str, object]], *, source_mode: str = "live"
    ) -> None:
        (destination / f"{name}.metadata.json").write_text(
            json.dumps(
                {
                    "dataset": name,
                    "source_name": "Phase 1 static fixture",
                    "source_url": "https://example.invalid/phase-1-fixture",
                    "source_mode": source_mode,
                    "source_detail": "static_test_literal",
                    "refreshed_at_utc": "2026-08-23T12:00:00+00:00",
                    "record_count": len(rows),
                    "fields": list(rows[0]),
                    "notes": [],
                    "reuse_policy": {
                        "status": "open-attribution",
                        "license": "CC BY",
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

    censo_rows = [
        {
            "codigo_region": row["codigo_region"],
            "nombre_region": row["nombre_region"],
            "codigo_provincia": row["codigo_provincia"],
            "nombre_provincia": row["nombre_provincia"],
            "codigo_comuna": row["codigo_comuna"],
            "nombre_comuna": row["nombre_comuna"],
            "poblacion_censada": "100",
            "hombres": "50",
            "mujeres": "50",
            "razon_hombre_mujer": "100",
            "poblacion_0_14": "10",
            "poblacion_15_29": "20",
            "poblacion_30_44": "30",
            "poblacion_45_64": "20",
            "poblacion_65_mas": "20",
        }
        for row in commune_rows
    ]
    hogares_rows = [
        {
            "codigo_region": row["codigo_region"],
            "nombre_region": row["nombre_region"],
            "codigo_provincia": row["codigo_provincia"],
            "nombre_provincia": row["nombre_provincia"],
            "codigo_comuna": row["codigo_comuna"],
            "nombre_comuna": row["nombre_comuna"],
            "viviendas_censadas": "10",
            "viviendas_particulares_ocupadas": "8",
            "viviendas_particulares_desocupadas": "1",
            "viviendas_colectivas": "1",
            "hogares_censados": "8",
            "promedio_personas_hogar": "2.5",
        }
        for row in commune_rows
    ]
    electoral_rows = [
        {
            "codigo_comuna": row["codigo_comuna"],
            "nombre_comuna": row["nombre_comuna"],
            "distrito_electoral": "1",
            "circunscripcion_senatorial": "1",
        }
        for row in commune_rows
    ]
    finance_rows = [
        {
            "anio": "2024",
            "codigo_comuna": row["codigo_comuna"],
            "nombre_comuna": row["nombre_comuna"],
            "ingresos_totales": "100",
            "gastos_totales": "90",
            "ingresos_propios_permanentes": "50",
            "fondo_comun_municipal": "10",
            "gasto_personal": "20",
            "gasto_inversion": "10",
        }
        for row in commune_rows
    ]
    resultados_rows = [
        {
            "anio": "2024",
            "codigo_comuna": row["codigo_comuna"],
            "matricula_total": "100",
            "asistencia_promedio": "90",
            "tasa_aprobacion": "80",
            "tasa_reprobacion": "10",
            "tasa_retiro": "10",
            "establecimientos_reportados": "1",
        }
        for row in commune_rows
    ]
    siedu_rows = [
        {
            "anio": "2024",
            "codigo_comuna": row["codigo_comuna"],
            "codigo_indicador": "S1",
            "nombre_indicador": "Indicador sintetico",
            "categoria": "Prueba",
            "valor": "1.0",
            "unidad": "unidad",
            "fuente_original": "Prueba",
            "cobertura_tipo": "nacional",
        }
        for row in commune_rows
    ]
    health_rows = [
        {
            "codigo_establecimiento": "H1",
            "nombre_establecimiento": "Hospital uno",
            "tipo_establecimiento": "Hospital",
            "dependencia_administrativa": "Publica",
            "nivel_atencion": "Secundario",
            "codigo_region": "01",
            "nombre_region": "Region Uno",
            "codigo_comuna": "01001",
            "nombre_comuna": "Comuna 001",
            "tiene_servicio_urgencia": "SI",
            "tipo_urgencia": "General",
            "latitud": "-20.0",
            "longitud": "-70.0",
            "estado_funcionamiento": "Vigente",
        }
    ]
    education_rows = [
        {
            "rbd": "E1",
            "dv_rbd": "1",
            "nombre_establecimiento": "Escuela uno",
            "codigo_region": "01",
            "codigo_comuna": "01001",
            "dependencia_administrativa": "Publica",
            "latitud": "-20.0",
            "longitud": "-70.0",
            "estado_funcionamiento": "Vigente",
        }
    ]
    indicator_rows = [
        {"fecha": "2026-08-23", "codigo_indicador": code, "valor": value}
        for code, value in (
            ("uf", "1.0"),
            ("dolar", "2.0"),
            ("euro", "3.0"),
            ("utm", "4.0"),
            ("ipc", "5.0"),
        )
    ]
    required = {
        "comunas": commune_rows,
        "indicadores": indicator_rows,
        "censo_comunal": censo_rows,
        "establecimientos_salud": health_rows,
        "censo_hogares_viviendas": hogares_rows,
        "distritos_electorales": electoral_rows,
        "establecimientos_educacionales": education_rows,
        "finanzas_municipales": finance_rows,
        "resultados_educacionales": resultados_rows,
        "indicadores_urbanos_siedu": siedu_rows,
    }
    for name, rows in required.items():
        write_csv(name, rows)
        write_metadata(name, rows)

    if include_candidate:
        candidate_rows = [
            {
                "codigo_region": "01",
                "codigo_comuna": "01001",
                "nombre_comuna": "Comuna 001",
                "anio": "2024",
                "tipo_cliente": "Residencial",
                "consumo_kwh": "100.0",
                "numero_clientes": "10",
                "fuente": "Phase 1 fallback fixture",
                "url_fuente": "",
                "fecha_fuente": "",
            }
        ]
        write_csv("consumo_electrico_comunal", candidate_rows)
        write_metadata("consumo_electrico_comunal", candidate_rows, source_mode="fallback")
