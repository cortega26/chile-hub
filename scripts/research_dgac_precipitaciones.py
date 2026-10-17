"""Candidato de investigación: precipitaciones diarias DGAC (2024-2025).

Fuente primaria: archivos CSV mensuales publicados por la DGAC en datos.gob.cl.
NO forma parte del bundle estable de chile-hub. Uso manual y fail-loud.
No atribuir georreferenciación comunal a estaciones sin código CUT verificado.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
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
PACKAGES = {
    (2024, 1): "precipitaciones-2024",
    (2024, 2): "precipitaciones-2do-semestre-del-ano-2024",
    (2025, 1): "precipitacion-1er-semestre-2025",
    (2025, 2): "precipitaciones-2do-semestre-2025",
}
COLUMNS = (
    "fecha", "id_estacion", "nombre_estacion", "latitud_dms", "altitud_m",
    "precipitacion_mm", "url_fuente", "licencia_fuente",
)
RESOURCE_RE = re.compile(r"precipitacion[_ ](\d{2})(\d{4})\.csv", re.IGNORECASE)
MISSING = frozenset(("", "S/I", "S/D", "NA", "N/A", "NULL", "-", "///"))


class SourceError(ValueError):
    """El origen cambió, está incompleto o no cumple su contrato."""


def _request(url: str, *, retries: int = 3) -> bytes:
    for attempt in range(retries):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "chile-hub-research/1.0 (+https://github.com/cortega26/chile-hub)"}
            )
            with urllib.request.urlopen(request, timeout=35) as response:
                return response.read()
        except (OSError, urllib.error.URLError) as exc:
            if attempt == retries - 1:
                raise SourceError(f"No se pudo descargar {url}: {exc}") from exc
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def _package(name: str) -> dict[str, Any]:
    # IDs de paquetes estables, NO búsqueda por títulos ambiguos.
    from urllib.parse import quote

    url = f"{API}/package_show?id={quote(name)}"
    payload = json.loads(_request(url))
    if payload.get("success") is not True or not isinstance(payload.get("result"), dict):
        raise SourceError(f"CKAN no devolvió el paquete {name}")
    return payload["result"]


def resources_for_package(package: dict[str, Any], year: int, months: range) -> list[dict[str, str]]:
    """Exige exactamente un CSV por cada mes, sin deduplicar arbitrariamente."""
    resources: dict[int, dict[str, str]] = {}
    for item in package.get("resources", []):
        name = str(item.get("name", "")).strip()
        match = RESOURCE_RE.search(name)
        if not match or item.get("format", "").lower() != "csv":
            continue
        month, item_year = map(int, match.groups())
        if item_year != year or month not in months:
            continue
        if month in resources:
            raise SourceError(f"Dos recursos CSV para {year}-{month:02d}")
        url = item.get("url", "")
        if not url.startswith("https://datos.gob.cl/"):
            raise SourceError(f"URL no oficial para {name}: {url}")
        resources[month] = {"url": url, "name": name}
    missing = set(months) - set(resources)
    if missing:
        raise SourceError(f"Faltan CSV del año {year}, meses: {sorted(missing)}")
    return [resources[m] for m in sorted(resources)]


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


def parse_csv(payload: bytes, *, year: int, month: int, url: str, license_id: str) -> list[dict[str, str]]:
    """Lee 8 columnas *sin cabecera*; CKAN suele tomar la primera fila como header."""
    content = _decode(payload)
    try:
        dialect = csv.Sniffer().sniff(content[:4096], delimiters=",;\t")
    except csv.Error as exc:
        raise SourceError(f"Separador CSV no detectable ({year}-{month:02d})") from exc
    result: list[dict[str, str]] = []
    for line, cells in enumerate(csv.reader(io.StringIO(content), dialect), start=1):
        if not cells or all(not c.strip() for c in cells):
            continue
        if line == 1 and not cells[0].strip().isdigit():
            # Algunos archivos futuros podrían traer encabezados; nunca inferirlos por CKAN.
            if len(cells) == 8 and "estacion" in cells[0].lower().replace("ó", "o"):
                continue
            raise SourceError(f"Primera fila desconocida ({year}-{month:02d}): {cells!r}")
        if len(cells) != 8:
            raise SourceError(f"{year}-{month:02d}:{line} esperaba 8 columnas; recibió {len(cells)}")
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
                "latitud_dms": lat,
                "altitud_m": str(altitude),
                "precipitacion_mm": "" if precip is None else str(precip),
                "url_fuente": url,
                "licencia_fuente": license_id,
            }
        )
    if len(result) < 100:
        raise SourceError(f"{year}-{month:02d}: solo {len(result)} filas; posible cambio de fuente")
    return result


def harvest(output: Path) -> dict[str, Any]:
    """Obtiene todos los meses o falla sin publicar un resultado incompleto."""
    all_rows: list[dict[str, str]] = []
    source_files = []
    seen: set[tuple[str, str]] = set()
    for (year, semester), name in PACKAGES.items():
        package = _package(name)
        license_id = str(package.get("license_id", ""))
        if license_id not in ("cc-by", "cc-zero"):
            raise SourceError(f"Licencia inesperada {name}: {license_id!r}")
        months = range(1, 7) if semester == 1 else range(7, 13)
        for resource in resources_for_package(package, year, months):
            match = RESOURCE_RE.search(resource["name"])
            assert match is not None
            month = int(match.group(1))
            payload = _request(resource["url"])
            parsed = parse_csv(
                payload, year=year, month=month, url=resource["url"], license_id=license_id
            )
            for row in parsed:
                key = (row["fecha"], row["id_estacion"])
                if key in seen:
                    raise SourceError(f"Duplicado estación-fecha: {key}")
                seen.add(key)
            all_rows.extend(parsed)
            source_files.append(
                {
                    "url": resource["url"],
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "rows": len(parsed),
                    "license": license_id,
                }
            )
    if len(source_files) != 24:
        raise SourceError(f"Esperaba 24 meses; encontré {len(source_files)}")
    all_rows.sort(key=lambda row: (row["fecha"], row["id_estacion"]))
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(all_rows)
    data = buffer.getvalue().encode("utf-8")
    metadata = {
        "dataset": "precipitaciones_dgac",
        "publication_track": "candidate",
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "source_name": SOURCE,
        "source_url": "https://datos.gob.cl/organization/direccion_general_de_aeronautica_civil",
        "source_mode": "live",
        "period": "2024-01-01/2025-12-31",
        "months": 24,
        "record_count": len(all_rows),
        "station_count": len({row["id_estacion"] for row in all_rows}),
        "missing_measurements": sum(row["precipitacion_mm"] == "" for row in all_rows),
        "fields": list(COLUMNS),
        "sha256": hashlib.sha256(data).hexdigest(),
        "source_files": source_files,
        "notes": [
            "Mediciones en estaciones; sin CUT comunal ni interpolación espacial.",
            "Los datos faltantes se conservan vacíos, no se convierten en cero.",
            "2024-I CC BY; demás paquetes CC0 al momento de la inspección.",
            "Candidato: fuera del bundle hasta validar extracción end-to-end y contratos.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # Escribir solo cuando los 24 meses hayan superado todas las validaciones.
    tmp_csv = output.with_suffix(output.suffix + ".tmp")
    tmp_json = output.with_suffix(".metadata.json.tmp")
    tmp_csv.write_bytes(data)
    tmp_json.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_csv.replace(output)
    tmp_json.replace(output.with_suffix(".metadata.json"))
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] /
        "data" / "research" / "precipitaciones_dgac_2024_2025.csv",
    )
    args = parser.parse_args()
    meta = harvest(args.output)
    print(json.dumps({key: meta[key] for key in (
        "dataset", "period", "record_count", "station_count", "sha256"
    )}, ensure_ascii=False))


if __name__ == "__main__":
    main()
