"""Prueba reproducible de valor con artefactos publicados de chile-hub.

No usa red ni telemetría; no compara rendimiento con otros portales.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter_ns
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASETS = (
    "comunas",
    "censo_comunal",
    "censo_hogares_viviendas",
    "perfil_territorial_comunal",
    "pobreza_comunal",
)
CUT_PATTERN = re.compile(r"\d{5}\Z")


def read_rows(directory: Path, name: str) -> list[dict[str, Any]]:
    """Lee una capa real, exigiendo JSON de filas con CUT válidos."""
    path = directory / f"{name}.json"
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se puede leer {path}: {exc}") from exc
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{name}: se esperaba una lista JSON no vacía")
    for position, row in enumerate(rows):
        if not isinstance(row, dict) or not CUT_PATTERN.fullmatch(
            str(row.get("codigo_comuna", ""))
        ) or not isinstance(row.get("codigo_comuna"), str):
            raise ValueError(f"{name}: CUT inválido en fila {position}")
    return rows


def unique_by_cut(rows: list[dict[str, Any]], name: str) -> dict[str, dict[str, Any]]:
    """Impide que un join multiplique registros por claves duplicadas."""
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["codigo_comuna"]
        if key in index:
            raise ValueError(f"{name}: CUT duplicado: {key}")
        index[key] = row
    return index


def coverage(base: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    """Informa cobertura y huecos sin imputaciones."""
    present = sorted(base.keys() & other.keys())
    missing = sorted(base.keys() - other.keys())
    extra = sorted(other.keys() - base.keys())
    return {
        "total_comunas": len(base),
        "comunas_cruzadas": len(present),
        "cobertura_pct": round(100 * len(present) / len(base), 2),
        "cut_sin_cruce": missing,
        "cut_fuera_de_base": extra,
    }


def case_censo(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Cruza la división político-administrativa con población censada INE 2024."""
    base = unique_by_cut(data["comunas"], "comunas")
    censo = unique_by_cut(data["censo_comunal"], "censo_comunal")
    coverage_info = coverage(base, censo)
    top = []
    for cut in base.keys() & censo.keys():
        row = censo[cut]
        population = row["poblacion_censada"]
        older = row["poblacion_65_mas"]
        if not isinstance(population, int) or population <= 0:
            raise ValueError(f"Censo 2024: población inválida en {cut}")
        if not isinstance(older, int) or not 0 <= older <= population:
            raise ValueError(f"Censo 2024: tramo 65+ inválido en {cut}")
        top.append({
            "codigo_comuna": cut,
            "comuna": base[cut]["nombre_comuna"],
            "porcentaje_65_mas": round(100 * older / population, 2),
        })
    top.sort(key=lambda r: (-r["porcentaje_65_mas"], r["codigo_comuna"]))
    return {
        **coverage_info,
        "poblacion_censada_en_cruce": sum(censo[c]["poblacion_censada"] for c in base.keys() & censo.keys()),
        "ejemplo_top_65_mas": top[:3],
        "nota": "Censo INE 2024; ranking descriptivo, no causal.",
    }


def case_hogares(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Cruza comunas con hogares/viviendas INE 2024, agrupando por región."""
    base = unique_by_cut(data["comunas"], "comunas")
    homes = unique_by_cut(data["censo_hogares_viviendas"], "censo_hogares_viviendas")
    coverage_info = coverage(base, homes)
    regions: dict[str, dict[str, Any]] = {}
    for cut in base.keys() & homes.keys():
        households = homes[cut]["hogares_censados"]
        dwellings = homes[cut]["viviendas_censadas"]
        if not isinstance(households, int) or households < 0 or not isinstance(dwellings, int) or dwellings < 0:
            raise ValueError(f"Hogares 2024: recuento inválido en {cut}")
        code = base[cut]["codigo_region"]
        region = regions.setdefault(code, {"codigo_region": code, "hogares": 0, "viviendas": 0})
        region["hogares"] += households
        region["viviendas"] += dwellings
    largest = sorted(regions.values(), key=lambda r: (-r["hogares"], r["codigo_region"]))
    return {
        **coverage_info,
        "regiones_con_datos": len(regions),
        "hogares_censados_en_cruce": sum(r["hogares"] for r in regions.values()),
        "viviendas_censadas_en_cruce": sum(r["viviendas"] for r in regions.values()),
        "ejemplo_regiones": largest[:3],
        "nota": "Censo INE 2024; categorías hogares y viviendas no son equivalentes.",
    }


def case_pobreza(data: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Cruza perfil territorial y pobreza SAE 2022 sin equiparar años."""
    base = unique_by_cut(data["perfil_territorial_comunal"], "perfil_territorial_comunal")
    selected = [r for r in data["pobreza_comunal"] if r.get("dimension") == "ingresos" and r.get("anio") == 2022]
    if not selected:
        raise ValueError("Pobreza: no existe la serie SAE ingresos 2022")
    poverty = unique_by_cut(selected, "pobreza_comunal ingresos 2022")
    coverage_info = coverage(base, poverty)
    sample = []
    for cut in base.keys() & poverty.keys():
        rate = poverty[cut]["tasa"]
        if not isinstance(rate, (int, float)) or not 0 <= rate <= 100:
            raise ValueError(f"Pobreza 2022: tasa fuera de rango en {cut}")
        sample.append({
            "codigo_comuna": cut,
            "comuna": base[cut]["nombre_comuna"],
            "tasa_pobreza_ingresos_2022_pct": round(rate, 2),
            "poblacion_censada_2024": base[cut].get("poblacion_censada"),
        })
    sample.sort(key=lambda r: r["codigo_comuna"])
    return {
        **coverage_info,
        "ejemplo_cruce": sample[:3],
        "nota": "SAE 2022 + Censo 2024: cortes distintos; no implica causalidad ni tasa actualizada.",
    }


CASES: tuple[tuple[str, tuple[str, ...], Callable[[dict[str, list[dict[str, Any]]]], dict[str, Any]]], ...] = (
    ("censo_y_territorio", ("comunas", "censo_comunal"), case_censo),
    ("hogares_por_region", ("comunas", "censo_hogares_viviendas"), case_hogares),
    ("perfil_y_pobreza", ("perfil_territorial_comunal", "pobreza_comunal"), case_pobreza),
)


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run_proof(directory: Path, runs: int = 5, expected_communes: int = 346) -> dict[str, Any]:
    """Ejecuta tres tareas y compara la salida de cada repetición byte a byte."""
    if runs < 1 or expected_communes < 1:
        raise ValueError("runs y expected_communes deben ser positivos")
    artifacts: list[dict[str, Any]] = []
    for name in DATASETS:
        path = directory / f"{name}.json"
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise ValueError(f"No existe artefacto {path}: {exc}") from exc
        artifacts.append({"dataset": name, "sha256": sha256_hex(payload), "bytes": len(payload)})
    evidence = []
    for title, inputs, task in CASES:
        elapsed_ms = []
        first_result = None
        for _ in range(runs):
            started = perf_counter_ns()
            data = {name: read_rows(directory, name) for name in inputs}
            result = task(data)
            elapsed_ms.append(round((perf_counter_ns() - started) / 1e6, 3))
            if result["total_comunas"] != expected_communes:
                raise ValueError(f"{title}: {result['total_comunas']} comunas, esperadas {expected_communes}")
            if first_result is None:
                first_result = result
            elif result != first_result:
                raise ValueError(f"{title}: resultados no deterministas")
        assert first_result is not None
        canonical = json.dumps(first_result, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        evidence.append({
            "caso": title,
            "entradas": list(inputs),
            "resultado": first_result,
            "resultado_sha256": sha256_hex(canonical.encode("utf-8")),
            "duracion_ms": {
                "min": min(elapsed_ms),
                "mediana": round(statistics.median(elapsed_ms), 3),
                "max": max(elapsed_ms),
                "repeticiones": runs,
            },
        })
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL, text=True, timeout=3
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        git_sha = None
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_commit": git_sha,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "sources": artifacts,
        "cases": evidence,
        "interpretacion": (
            "Tiempos locales de lectura JSON, cruce y calculo; NO son ahorro frente a la fuente "
            "ni comparacion con datos.gob.cl u otra plataforma. Cobertura = claves CUT presentes."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data" / "normalized")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--output", type=Path, help="Ruta opcional del informe JSON (fuera de data/normalized)")
    args = parser.parse_args(argv)
    try:
        report = run_proof(args.data_dir.resolve(), runs=args.runs)
        if args.output:
            out = args.output.resolve()
            if out.is_relative_to((PROJECT_ROOT / "data" / "normalized").resolve()):
                raise ValueError("El informe no puede sobrescribir artefactos de data/normalized")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print("Chile Hub — evidencia reproducible (sin comparación externa)")
    for case in report["cases"]:
        coverage_info = case["resultado"]
        print(f"{case['caso']}: {coverage_info['comunas_cruzadas']}/{coverage_info['total_comunas']} "
              f"CUT ({coverage_info['cobertura_pct']}%); mediana {case['duracion_ms']['mediana']} ms")
    if args.output:
        print(f"Informe: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
