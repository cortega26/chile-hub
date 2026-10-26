"""Política de publicación parcial (plan 150, ADR-025).

Un dataset `stable_publishable` que en este build no califica para publicar
(fuente en fallback, o caída de `record_count` sobre el umbral) ya **no**
bloquea las demás capas. En su lugar se **retiene** su última versión buena,
se marca en el catálogo y se cuenta para el escalamiento.

Estados por build:

- `fresh`: cumple; publica su artefacto nuevo.
- `held`: no cumple, pero existe artefacto publicado previo; se publica el
  previo, marcado con `publication_hold`.
- `unrecoverable`: no cumple y no hay artefacto previo; el build falla.

El invariante de AGENTS.md §4.2 —"nunca publicar datos degradados"— se mantiene
intacto: un `held` publica el dato anterior, nunca el degradado. Lo que se acota
es el radio de impacto de una fuente caída.

La clasificación es una función pura sobre metadatos ya cargados: el build y el
verificador llaman a `evaluate_holds()`, no a dos implementaciones distintas.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime

import polars as pl

from src.builders._shared import NON_FALLBACK_SOURCE_MODES, NORMALIZED_DIR

# Tras N días retenido el build falla: una degradación no puede volverse
# silenciosa ni permanente. El umbral es **temporal**, no por número de builds:
# varios builds el mismo día (un dispatch de diagnóstico, un rebase, un rerun)
# inflaban un contador por build y disparaban el tope en horas. Mismo orden de
# magnitud que la ventana del issue automático de schedule.
MAX_HELD_DAYS = 7

# Alias histórico: el contador por build se conserva en el artefacto como dato
# informativo, pero ya no decide el escalamiento.
MAX_HELD_BUILDS = MAX_HELD_DAYS

# Mismo umbral que `verify_pipeline.DEFAULT_MAX_RECORD_DROP_PCT`; vive aquí para
# que build y verificador no puedan divergir.
DEFAULT_MAX_RECORD_DROP_PCT = 20.0

# dataset del catálogo -> clave en el dict de frames de load_staging_inputs().
# `comunas_enriquecidas` queda fuera a propósito: es un alias de `comunas` y
# hereda su frame, así que retenerlo por separado sería inconsistente.
DATASET_FRAME_KEYS: dict[str, str] = {
    "regiones": "regiones",
    "provincias": "provincias",
    "comunas": "comunas",
    "indicadores": "indicadores",
    "censo_comunal": "censo",
    "establecimientos_salud": "salud",
    "censo_hogares_viviendas": "censo_hogares",
    "distritos_electorales": "electoral",
    "establecimientos_educacionales": "educacionales",
    "finanzas_municipales": "finanzas",
    "resultados_educacionales": "resultados_educacionales",
    "indicadores_urbanos_siedu": "siedu",
    "empresas": "empresas",
    "pobreza_comunal": "pobreza_comunal",
    "consumo_electrico_comunal": "consumo_electrico",
    "partidos_politicos": "partidos_politicos",
    "autoridades_electas": "autoridades_electas",
    "estadisticas_vitales": "estadisticas_vitales",
    "permisos_edificacion": "permisos_edificacion",
    "calidad_aire": "calidad_aire",
    "precipitaciones_dgac": "precipitaciones_dgac",
    "perfil_territorial_comunal": "perfil_territorial",
}

# Datasets que no se publican desde el build diario: no participan de la
# retención porque no tienen artefacto propio que conservar.
NOT_HOLDABLE = {"comunas_enriquecidas"}


@dataclass(frozen=True)
class HoldDecision:
    """Un dataset que este build no puede refrescar y se publica retenido."""

    dataset: str
    frame_key: str
    reason: str
    previous: dict = field(default_factory=dict)

    @property
    def builds_held(self) -> int:
        hold = self.previous.get("publication_hold") or {}
        return int(hold.get("builds_held") or 0) + 1


def _load_previous_catalog(normalized_dir: str | None = None) -> dict:
    """Catálogo publicado en el checkout (build anterior); vacío si no existe."""
    path = os.path.join(normalized_dir or NORMALIZED_DIR, "dataset_catalog.json")
    try:
        with open(path, encoding="utf-8") as f:
            catalog = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return {entry.get("dataset"): entry for entry in catalog.get("datasets", [])}


def _required_frame_keys(registry) -> set[str]:
    return {
        entry["dataset"]
        for entry in registry
        if entry.get("publication_track") == "stable_publishable"
        and entry.get("public_bundle_eligible") is True
    }


def evaluate_holds(
    metadata: dict,
    registry,
    normalized_dir: str | None = None,
    max_record_drop_pct: float = DEFAULT_MAX_RECORD_DROP_PCT,
) -> dict[str, HoldDecision]:
    """Decide qué datasets `stable_publishable` se retienen en este build.

    `metadata` está indexado por clave de frame (ver `DATASET_FRAME_KEYS`).
    Devuelve solo los retenidos; el resto se considera publicable y lo valida
    `verify_pipeline` con su propia lógica de frescura.
    """
    previous_catalog = _load_previous_catalog(normalized_dir)
    holds: dict[str, HoldDecision] = {}
    if not previous_catalog:
        # Primer build (o staging sintético de tests): no hay nada que retener.
        # Sin catálogo previo la retención no aplica y el comportamiento es el
        # de siempre.
        return holds

    for dataset in sorted(_required_frame_keys(registry)):
        if dataset in NOT_HOLDABLE:
            continue
        frame_key = DATASET_FRAME_KEYS.get(dataset)
        if frame_key is None:
            continue
        meta = metadata.get(frame_key)
        if not meta:
            continue
        previous = previous_catalog.get(dataset) or {}
        reasons = []

        source_mode = meta.get("source_mode")
        if source_mode not in NON_FALLBACK_SOURCE_MODES:
            reasons.append(f"source_mode={source_mode}")

        previous_count = previous.get("record_count")
        current_count = meta.get("record_count")
        if (
            isinstance(previous_count, int)
            and previous_count > 0
            and isinstance(current_count, int)
        ):
            drop_pct = (previous_count - current_count) / previous_count * 100
            if drop_pct > max_record_drop_pct:
                reasons.append(
                    f"record_count cayó {drop_pct:.1f}% ({previous_count} -> {current_count})"
                )

        if not reasons:
            continue
        holds[dataset] = HoldDecision(
            dataset=dataset,
            frame_key=frame_key,
            reason="; ".join(reasons),
            previous=previous,
        )
    return holds


def _previous_parquet_path(dataset: str, normalized_dir: str | None = None) -> str:
    return os.path.join(normalized_dir or NORMALIZED_DIR, f"{dataset}.parquet")


def held_days(hold: dict, now: datetime | None = None) -> float:
    """Días transcurridos desde la primera retención; `inf` si no hay marca."""
    since = (hold or {}).get("since_utc")
    if not since:
        return float("inf")
    try:
        started = datetime.fromisoformat(since)
    except ValueError:
        return float("inf")
    reference = now or datetime.now(UTC)
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    return (reference - started).total_seconds() / 86400


def hold_errors(
    holds: dict[str, HoldDecision],
    *,
    normalized_dir: str | None = None,
    max_held_days: float = MAX_HELD_DAYS,
    now: datetime | None = None,
) -> list[str]:
    """Errores que hacen fallar el build antes de publicar cualquier cosa."""
    errors = []
    for dataset, decision in sorted(holds.items()):
        if not decision.previous:
            errors.append(
                f"{dataset}: no califica para publicar ({decision.reason}) y no existe "
                "artefacto publicado previo que retener"
            )
            continue
        if not decision.previous.get("refreshed_at_utc"):
            errors.append(f"{dataset}: el artefacto previo no declara refreshed_at_utc")
        if not os.path.exists(_previous_parquet_path(dataset, normalized_dir)):
            errors.append(f"{dataset}: falta {dataset}.parquet del build anterior")
        # El escalamiento se mide desde la PRIMERA retención. Un hold nuevo
        # (sin marca previa) empieza en 0 días: si no, `held_days` devolvería
        # infinito y el primer build ya fallaría.
        previous_hold = decision.previous.get("publication_hold")
        days = held_days(previous_hold, now=now) if previous_hold else 0.0
        if days > max_held_days:
            errors.append(
                f"{dataset}: retenido {days:.1f} días (tope {max_held_days:g}). La fuente "
                "no se recuperó: hay que decidir entre repararla, sacarla del carril "
                "stable_publishable o retirarla (AGENTS.md §6)."
            )
    return errors


def apply_holds(
    frames: dict,
    metadata: dict,
    holds: dict[str, HoldDecision],
    *,
    normalized_dir: str | None = None,
    attempted_at_utc: str | None = None,
) -> None:
    """Sustituye frames y metadatos por la última versión buena, marcada.

    Se aplica **antes** de construir cualquier formato, para que parquet, JSON,
    DuckDB, SQLite y Excel salgan consistentes: un dataset retenido nunca se
    mezcla con datos degradados en el mismo entregable.
    """
    for dataset, decision in sorted(holds.items()):
        frame = pl.read_parquet(_previous_parquet_path(dataset, normalized_dir))
        frames[decision.frame_key] = frame
        base = dict(metadata.get(decision.frame_key) or {})
        previous = decision.previous
        # La procedencia que se publica es la del artefacto retenido, no la del
        # intento fallido de hoy.
        for key in ("source_name", "source_url", "source_mode", "source_detail"):
            if previous.get(key) is not None:
                base[key] = previous[key]
        if previous.get("refreshed_at_utc"):
            base["refreshed_at_utc"] = previous["refreshed_at_utc"]
        base["record_count"] = frame.height
        base["publication_hold"] = {
            "retained": True,
            "reason": decision.reason,
            "attempted_at_utc": attempted_at_utc,
            "previous_generated_at_utc": previous.get("refreshed_at_utc"),
            "since_utc": (previous.get("publication_hold") or {}).get("since_utc")
            or attempted_at_utc,
            "builds_held": decision.builds_held,
        }
        metadata[decision.frame_key] = base
