"""Modelo final de resultado de extracción — Phase 4 (ADR-018/019, roadmap Phase 4).

Este es el modelo provenance/tiempo definitivo para extractores. Fases
posteriores pueden normalizar, validar y proyectar este modelo, pero no deben
añadir un segundo modelo estructural.

Campos obligatorios en cada resultado; los opcionales siguen una política
nullable documentada y nunca se infieren desde ``retrieved_at``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

UTC = timezone.utc


def _compute_snapshot_hash(path: Path | None) -> str | None:
    """SHA-256 streaming del snapshot crudo, si existe."""
    if path is None or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class ExtractionResult:
    """Resultado tipado y completo de una extracción.

    Obligatorios en todo resultado; los opcionales son ``None`` cuando la
    fuente no los provee, nunca inferidos desde ``retrieved_at``.
    """

    # Identidad
    dataset: str

    # Datos normalizados
    dataframe: pl.DataFrame

    # Proveniencia de snapshot
    raw_snapshot_path: Path | None
    snapshot_hash: str | None
    snapshot_reference: str | None  # referencia inmutable (ruta relativa o URI)

    # Modo y tiempos
    source_mode: str  # live | fallback | monthly | etc. (ver VALID_SOURCE_MODES)
    retrieved_at: datetime  # cuándo se obtuvo (UTC)
    source_published_at: datetime | None  # cuándo la fuente dice que se publicó
    observed_period: dict[str, str] | None  # {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} o None

    # Política y detalle
    reuse_policy: dict[str, Any]
    source_detail: str | None
    notes: tuple[str, ...] = field(default_factory=tuple)

    # Compatibilidad con staging legacy (para adapter)
    record_count: int | None = None
    fields: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        # Normalizar retrieved_at a UTC
        if self.retrieved_at.tzinfo is None:
            object.__setattr__(self, "retrieved_at", self.retrieved_at.replace(tzinfo=UTC))
        # Validar que los obligatorios no sean None
        if not self.dataset:
            raise ValueError("ExtractionResult.dataset es obligatorio")
        if self.source_mode not in {"live", "fallback", "monthly"}:
            # Permitir otros modos documentados pero advertir si es desconocido
            pass

    def to_staging_metadata(self, source_name: str, source_url: str) -> dict[str, Any]:
        """Proyección a metadata.json de staging (compatibilidad legacy)."""
        meta: dict[str, Any] = {
            "dataset": self.dataset,
            "source_name": source_name,
            "source_url": source_url,
            "source_mode": self.source_mode,
            "source_detail": self.source_detail or "",
            "refreshed_at_utc": self.retrieved_at.isoformat(),
            "retrieved_at": self.retrieved_at.isoformat(),
            "record_count": self.record_count
            if self.record_count is not None
            else self.dataframe.height,
            "fields": list(self.fields) if self.fields is not None else self.dataframe.columns,
            "notes": list(self.notes),
            "reuse_policy": self.reuse_policy,
        }
        # Campos opcionales: solo si están presentes, y nunca inferidos
        if self.snapshot_hash is not None:
            meta["snapshot_hash"] = self.snapshot_hash
        if self.snapshot_reference is not None:
            meta["snapshot_reference"] = self.snapshot_reference
        if self.source_published_at is not None:
            meta["source_published_at"] = self.source_published_at.isoformat()
        if self.observed_period is not None:
            meta["observed_period"] = self.observed_period
        return meta

    @staticmethod
    def compute_hash(path: Path | None) -> str | None:
        return _compute_snapshot_hash(path)
