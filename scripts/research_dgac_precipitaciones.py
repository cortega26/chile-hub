"""Candidato de investigación: precipitaciones diarias DGAC (2013-2026).

Fuente primaria: archivos CSV mensuales publicados por la DGAC en datos.gob.cl.
NO forma parte del bundle estable de chile-hub. Uso manual y fail-loud.
No atribuir georreferenciación comunal a estaciones sin código CUT verificado.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import io
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API = "https://datos.gob.cl/api/3/action"
SOURCE = "Dirección General de Aeronáutica Civil (DGAC) — datos.gob.cl"
# Se fijan paquetes concretos (sin búsqueda fuzzy durante la cosecha) para evitar
# confundir series de temperatura y paquetes duplicados de 2015/2025.
# 2014 y 2015-I aparecen en un paquete legado CC-NC; quedan excluidos.
PACKAGES = {
    (2013, 1): "precipitaciones-primer-semestre-2013",
    (2013, 2): "precipitaciones-segundo-semestre-2013",
    (2015, 2): "precipitacion-2o-semestre-2015",
    **{
        (year, half): f"precipitaciones-{period}-semestre-{year}"
        for year in range(2016, 2024)
        for half, period in ((1, "primer"), (2, "segundo"))
    },
    (2024, 1): "precipitaciones-2024",
    (2024, 2): "precipitaciones-2do-semestre-del-ano-2024",
    (2025, 1): "precipitacion-1er-semestre-2025",
    (2025, 2): "precipitaciones-2do-semestre-2025",
    (2026, 1): "precipitacion-1er-semestre-2026",
}
# Esta lista representa huecos de *redistribución*, no prueba ausencia de
# observaciones. El paquete legacy CKAN 2719 declara CC-NC.
EXCLUDED_SOURCE_PERIODS = {
    "2014": "2014 disponible en paquete legacy 2719 CC-NC; excluido por licencia",
    "2015-01/2015-06": "2015-I disponible en paquete legacy 2719 CC-NC; excluido",
    "2026-07/2026-12": "2026-II aún no figura como paquete mensual en la fuente",
}
COLUMNS = (
    "fecha",
    "id_estacion",
    "nombre_estacion",
    "latitud_dms",
    "altitud_m",
    "precipitacion_mm",
    "url_fuente",
    "licencia_fuente",
)
RESOURCE_RE = re.compile(r"precipitacion[_ ]?(\d{2})(\d{4})(?:\d)?\.csv$", re.IGNORECASE)
MISSING = frozenset(("", "S/I", "S/D", "NA", "N/A", "NULL", "-", "///"))


class SourceError(ValueError):
    """El origen cambió, está incompleto o no cumple su contrato."""


def _request(url: str, *, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "chile-hub-research/1.0 (+https://github.com/cortega26/chile-hub)"
                },
            )
            with urllib.request.urlopen(request, timeout=35) as response:
                return response.read()
        except (OSError, urllib.error.URLError) as exc:
            if attempt == retries - 1:
                raise SourceError(f"No se pudo descargar {url}: {exc}") from exc
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _package(name: str) -> dict[str, Any]:
    # IDs de paquetes estables, NO búsqueda por títulos ambiguos.
    from urllib.parse import quote

    url = f"{API}/package_show?id={quote(name)}"
    payload = json.loads(_request(url))
    if payload.get("success") is not True or not isinstance(payload.get("result"), dict):
        raise SourceError(f"CKAN no devolvió el paquete {name}")
    return payload["result"]


def _resource_month(resource: dict[str, Any], year: int) -> int | None:
    """Mes desde URL real, no desde nombre de recurso (variable en 2015/2023)."""
    from urllib.parse import urlparse

    url = str(resource.get("url", ""))
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "datos.gob.cl":
        raise SourceError(f"Recurso externo o inseguro: {url}")
    filename = parsed.path.rsplit("/", 1)[-1]
    match = RESOURCE_RE.fullmatch(filename)
    if not match:
        return None
    month, file_year = map(int, match.groups())
    if file_year != year or not 1 <= month <= 12:
        return None
    return month


def resources_for_package(
    package: dict[str, Any], year: int, months: range
) -> list[dict[str, str]]:
    """Exige cobertura mensual, pero conserva duplicados para comparar hashes."""
    grouped: dict[int, list[dict[str, str]]] = {}
    for item in package.get("resources", []):
        if str(item.get("format", "")).lower() != "csv":
            continue
        month = _resource_month(item, year)
        if month not in months:
            continue
        grouped.setdefault(month, []).append(
            {"url": str(item["url"]), "name": str(item.get("name", "")), "month": str(month)}
        )
    missing = set(months) - set(grouped)
    if missing:
        raise SourceError(f"Faltan CSV del año {year}, meses: {sorted(missing)}")
    return [
        candidate
        for month in sorted(grouped)
        for candidate in sorted(grouped[month], key=lambda r: r["url"])
    ]


def _decode(payload: bytes) -> str:
    try:
        return payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return payload.decode("cp1252")


def _number(value: str, *, nullable: bool = False) -> float | None:
    cleaned = value.strip()
    if cleaned.upper() in MISSING:
        if nullable:
            return None
        raise SourceError("Campo numérico obligatorio vacío")
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        parsed = float(cleaned)
    except ValueError as exc:
        raise SourceError(f"Valor numérico desconocido: {value!r}") from exc
    if not (float("-inf") < parsed < float("inf")):
        raise SourceError(f"Valor no finito: {value!r}")
    return parsed


def parse_csv(
    payload: bytes, *, year: int, month: int, url: str, license_id: str
) -> list[dict[str, str]]:
    """Lee 8 columnas *sin cabecera*; CKAN suele tomar la primera fila como header."""
    content = _decode(payload)
    # En archivos 2013 hay comas *dentro* de nombres, pero columnas separadas
    # por punto y coma; csv.Sniffer puede escoger erróneamente ','.
    first_line = content.splitlines()[0] if content.splitlines() else ""
    if first_line.count(";") >= 7:
        delimiter = ";"
    else:
        try:
            delimiter = csv.Sniffer().sniff(content[:4096], delimiters=",;\t").delimiter
        except csv.Error as exc:
            raise SourceError(f"Separador CSV no detectable ({year}-{month:02d})") from exc
    result: list[dict[str, str]] = []
    for line, cells in enumerate(
        csv.reader(io.StringIO(content), delimiter=delimiter), start=1
    ):
        if not cells or all(not c.strip() for c in cells):
            continue
        if line == 1 and not cells[0].strip().isdigit():
            # Algunos archivos futuros podrían traer encabezados; nunca inferirlos por CKAN.
            if len(cells) == 8 and "estacion" in cells[0].lower().replace("ó", "o"):
                continue
            raise SourceError(f"Primera fila desconocida ({year}-{month:02d}): {cells!r}")
        if len(cells) != 8:
            raise SourceError(
                f"{year}-{month:02d}:{line} esperaba 8 columnas; recibió {len(cells)}"
            )
        code, name, lat, alt, y, m, d, rain = [cell.strip() for cell in cells]
        if not re.fullmatch(r"\d{6}", code):
            raise SourceError(f"{year}-{month:02d}:{line}: código estación inválido {code!r}")
        if not name or not lat:
            raise SourceError(f"{year}-{month:02d}:{line}: estación o latitud ausente")
        try:
            observed = dt.date(int(y), int(m), int(d))
        except ValueError as exc:
            raise SourceError(f"{year}-{month:02d}:{line}: fecha inválida") from exc
        if (observed.year, observed.month) != (year, month):
            raise SourceError(f"{year}-{month:02d}:{line}: fecha fuera del período {observed}")
        altitude = _number(alt)
        precip = _number(rain, nullable=True)
        if precip is not None and precip < 0:
            raise SourceError(f"{year}-{month:02d}:{line}: precipitación negativa {precip}")
        result.append(
            {
                "fecha": observed.isoformat(),
                "id_estacion": code,
                "nombre_estacion": name,
                "latitud_dms": html.unescape(lat),
                "altitud_m": str(altitude),
                "precipitacion_mm": "" if precip is None else str(precip),
                "url_fuente": url,
                "licencia_fuente": license_id,
            }
        )
    if len(result) < 100:
        raise SourceError(f"{year}-{month:02d}: solo {len(result)} filas; posible cambio de fuente")
    return result


def harvest(output: Path, *, start_year: int = 2013, end_year: int = 2026) -> dict[str, Any]:
    """Cosecha los períodos abiertos declarados o falla sin publicar parcial.

    No se exige continuidad donde hay licencias distintas o períodos no
    publicados: se consignan como excluded_source_periods.
    """
    if not 2013 <= start_year <= end_year <= 2026:
        raise SourceError("Rango admitido: 2013 <= inicio <= fin <= 2026")
    packages = {key: name for key, name in PACKAGES.items() if start_year <= key[0] <= end_year}
    all_rows: list[dict[str, str]] = []
    source_files: list[dict[str, Any]] = []
    duplicate_resources: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for (year, semester), name in packages.items():
        package = _package(name)
        license_id = str(package.get("license_id", ""))
        if license_id not in ("cc-by", "cc-zero"):
            raise SourceError(f"Licencia no redistribuible {name}: {license_id!r}")
        months = range(1, 7) if semester == 1 else range(7, 13)
        resource_list = resources_for_package(package, year, months)
        hashes: dict[int, str] = {}
        for resource in resource_list:
            month = int(resource["month"])
            payload = _request(resource["url"])
            digest = hashlib.sha256(payload).hexdigest()
            if month in hashes:
                if hashes[month] != digest:
                    raise SourceError(
                        f"{year}-{month:02d}: recursos duplicados con contenido distinto"
                    )
                duplicate_resources.append(
                    {"year_month": f"{year}-{month:02d}", "url": resource["url"], "sha256": digest}
                )
                continue
            hashes[month] = digest
            parsed = parse_csv(
                payload,
                year=year,
                month=month,
                url=resource["url"],
                license_id=license_id,
            )
            for row in parsed:
                key = (row["fecha"], row["id_estacion"])
                if key in seen:
                    raise SourceError(f"Duplicado estación-fecha: {key}")
                seen.add(key)
            all_rows.extend(parsed)
            source_files.append(
                {
                    "year_month": f"{year}-{month:02d}",
                    "package": name,
                    "url": resource["url"],
                    "sha256": digest,
                    "rows": len(parsed),
                    "license": license_id,
                }
            )
    expected = sum(6 for _ in packages)
    if len(source_files) != expected:
        raise SourceError(f"Esperaba {expected} meses; encontré {len(source_files)}")
    all_rows.sort(key=lambda row: (row["fecha"], row["id_estacion"]))
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(all_rows)
    data = buffer.getvalue().encode("utf-8")
    years: dict[str, int] = {}
    for row in all_rows:
        year = row["fecha"][:4]
        years[year] = years.get(year, 0) + 1
    metadata = {
        "dataset": "precipitaciones_dgac",
        "publication_track": "candidate",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "source_name": SOURCE,
        "source_url": "https://datos.gob.cl/organization/direccion_general_de_aeronautica_civil",
        "source_mode": "live",
        "period": f"{min(row['fecha'] for row in all_rows)}/{max(row['fecha'] for row in all_rows)}",
        "months": len(source_files),
        "record_count": len(all_rows),
        "station_count": len({row["id_estacion"] for row in all_rows}),
        "missing_measurements": sum(row["precipitacion_mm"] == "" for row in all_rows),
        "counts_by_year": years,
        "excluded_source_periods": {
            key: reason
            for key, reason in EXCLUDED_SOURCE_PERIODS.items()
            if (key == "2014" and start_year <= 2014 <= end_year)
            or (key.startswith("2015") and start_year <= 2015 <= end_year)
            or (key.startswith("2026") and start_year <= 2026 <= end_year)
        },
        "duplicate_resources": duplicate_resources,
        "fields": list(COLUMNS),
        "sha256": hashlib.sha256(data).hexdigest(),
        "source_files": source_files,
        "notes": [
            "Estaciones observacionales; sin CUT comunal ni interpolación.",
            "No se imputa lluvia ni se sustituyen faltantes por ceros.",
            "2026 solo primer semestre; comparaciones anuales requieren años completos.",
            "2014/2015-I del catálogo legacy CC-NC excluidos; no se inventa continuidad.",
            "Licencia registrada por archivo; las diferencias requieren atribución adecuada.",
            "Fuera del bundle estable hasta validación de calidad longitudinal.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_csv = output.with_suffix(output.suffix + ".tmp")
    tmp_json = output.with_suffix(".metadata.json.tmp")
    tmp_csv.write_bytes(data)
    tmp_json.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tmp_csv.replace(output)
    tmp_json.replace(output.with_suffix(".metadata.json"))
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "data"
        / "research"
        / "precipitaciones_dgac_historico_2013_2026.csv",
    )
    parser.add_argument("--start-year", type=int, default=2013)
    parser.add_argument("--end-year", type=int, default=2026)
    args = parser.parse_args()
    meta = harvest(args.output, start_year=args.start_year, end_year=args.end_year)
    print(
        json.dumps(
            {
                key: meta[key]
                for key in ("dataset", "period", "record_count", "station_count", "sha256")
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
