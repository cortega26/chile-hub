"""Contrato de publicación parcial (plan 150, ADR-025).

Un dataset `stable_publishable` que no puede refrescarse no bloquea a las demás
capas: publica su última versión buena, marcada. Estos tests fijan las tres
propiedades que no pueden degradarse:

1. Un `held` publica el artefacto **anterior**, no el degradado.
2. Sin artefacto previo no hay retención: el build falla.
3. La retención escala a los 7 builds; no se puede volver silenciosa.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import polars as pl
import pytest

from scripts.verify_pipeline import _publication_hold_violations, verify_publication_policy
from src.builders.publication_gate import (
    MAX_HELD_DAYS,
    apply_holds,
    evaluate_holds,
    held_days,
    hold_errors,
)

REGISTRY = [
    {
        "dataset": "censo_comunal",
        "publication_track": "stable_publishable",
        "public_bundle_eligible": True,
        "fallback_policy": "allowed_for_dev_blocked_for_publication",
    },
    {
        "dataset": "comunas",
        "publication_track": "stable_publishable",
        "public_bundle_eligible": True,
        "fallback_policy": "allowed_for_dev_blocked_for_publication",
    },
]


def _previous_catalog(path, *, records=346, refreshed="2026-10-15T00:00:00+00:00", held=None):
    entry = {
        "dataset": "censo_comunal",
        "source_name": "INE",
        "source_url": "https://example.invalid",
        "source_mode": "live",
        "source_detail": "official_xlsx",
        "refreshed_at_utc": refreshed,
        "record_count": records,
    }
    if held is not None:
        entry["publication_hold"] = held
    path.mkdir(parents=True, exist_ok=True)
    (path / "dataset_catalog.json").write_text(
        json.dumps({"dataset_count": 1, "datasets": [entry]}), encoding="utf-8"
    )


def _previous_parquet(path, rows=346):
    path.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"codigo_comuna": [f"{i:05d}" for i in range(rows)]}).write_parquet(
        path / "censo_comunal.parquet"
    )


def _metadata(**overrides):
    base = {
        "censo": {
            "source_name": "INE",
            "source_url": "https://example.invalid",
            "source_mode": "fallback",
            "source_detail": "official_xlsx",
            "refreshed_at_utc": "2026-10-25T00:00:00+00:00",
            "record_count": 3,
        }
    }
    base["censo"].update(overrides)
    return base


def test_fallback_dataset_is_held_when_previous_artifact_exists(tmp_path):
    _previous_catalog(tmp_path)
    _previous_parquet(tmp_path)

    holds = evaluate_holds(_metadata(), REGISTRY, str(tmp_path))

    assert set(holds) == {"censo_comunal"}
    assert "source_mode=fallback" in holds["censo_comunal"].reason
    assert hold_errors(holds, normalized_dir=str(tmp_path)) == []


def test_record_drop_alone_also_triggers_a_hold(tmp_path):
    _previous_catalog(tmp_path)
    _previous_parquet(tmp_path)

    holds = evaluate_holds(_metadata(source_mode="live"), REGISTRY, str(tmp_path))

    assert set(holds) == {"censo_comunal"}
    assert "record_count cayó" in holds["censo_comunal"].reason


def test_healthy_dataset_is_not_held(tmp_path):
    _previous_catalog(tmp_path)
    _previous_parquet(tmp_path)

    holds = evaluate_holds(_metadata(source_mode="live", record_count=346), REGISTRY, str(tmp_path))

    assert holds == {}


def test_without_previous_catalog_the_policy_does_not_apply(tmp_path):
    """Primer build o staging sintético: no hay nada que retener."""
    assert evaluate_holds(_metadata(), REGISTRY, str(tmp_path)) == {}


def test_hold_without_previous_artifact_fails_closed(tmp_path):
    _previous_catalog(tmp_path)  # catálogo sí, parquet no

    holds = evaluate_holds(_metadata(), REGISTRY, str(tmp_path))
    errors = hold_errors(holds, normalized_dir=str(tmp_path))

    assert any("censo_comunal.parquet" in error for error in errors)


def test_hold_without_any_previous_entry_is_unrecoverable(tmp_path):
    (tmp_path / "dataset_catalog.json").write_text(
        json.dumps({"dataset_count": 0, "datasets": []}), encoding="utf-8"
    )

    assert evaluate_holds(_metadata(), REGISTRY, str(tmp_path)) == {}


def test_apply_holds_publishes_the_previous_artifact_and_marks_it(tmp_path):
    _previous_catalog(tmp_path)
    _previous_parquet(tmp_path)
    frames = {"censo": pl.DataFrame({"codigo_comuna": ["01101"]})}
    metadata = _metadata()
    holds = evaluate_holds(metadata, REGISTRY, str(tmp_path))

    apply_holds(
        frames,
        metadata,
        holds,
        normalized_dir=str(tmp_path),
        attempted_at_utc="2026-10-25T12:00:00+00:00",
    )

    # El frame publicado es el previo (346 filas), nunca el degradado (1 fila).
    assert frames["censo"].height == 346
    hold = metadata["censo"]["publication_hold"]
    assert hold["retained"] is True
    assert hold["builds_held"] == 1
    assert hold["previous_generated_at_utc"] == "2026-10-15T00:00:00+00:00"
    assert metadata["censo"]["source_mode"] == "live"


def test_builds_held_accumulates_across_builds(tmp_path):
    _previous_catalog(tmp_path, held={"retained": True, "builds_held": 3, "since_utc": "x"})
    _previous_parquet(tmp_path)

    holds = evaluate_holds(_metadata(), REGISTRY, str(tmp_path))

    assert holds["censo_comunal"].builds_held == 4


def test_escalation_is_time_based_not_build_based(tmp_path):
    """Muchos builds el mismo día no deben disparar el tope."""
    _previous_catalog(
        tmp_path,
        held={"retained": True, "builds_held": 99, "since_utc": "2026-10-25T00:00:00+00:00"},
    )
    _previous_parquet(tmp_path)

    holds = evaluate_holds(_metadata(), REGISTRY, str(tmp_path))
    errors = hold_errors(
        holds,
        normalized_dir=str(tmp_path),
        now=datetime.fromisoformat("2026-10-26T12:00:00+00:00"),
    )

    assert holds["censo_comunal"].builds_held == 100
    assert errors == []


def test_escalation_after_max_held_days_fails_closed(tmp_path):
    _previous_catalog(
        tmp_path,
        held={"retained": True, "builds_held": 1, "since_utc": "2026-10-01T00:00:00+00:00"},
    )
    _previous_parquet(tmp_path)

    holds = evaluate_holds(_metadata(), REGISTRY, str(tmp_path))
    errors = hold_errors(
        holds,
        normalized_dir=str(tmp_path),
        now=datetime.fromisoformat("2026-10-25T00:00:00+00:00"),
    )

    assert any("tope" in error for error in errors)


def test_marker_missing_required_fields_is_rejected():
    violations = _publication_hold_violations("censo_comunal", {"retained": True})

    assert any("reason" in v for v in violations)
    assert any("previous_generated_at_utc" in v for v in violations)
    assert any("builds_held" in v for v in violations)
    assert any("since_utc" in v for v in violations)


def test_marker_beyond_cap_is_rejected():
    old = (datetime.now(UTC) - timedelta(days=MAX_HELD_DAYS + 1)).isoformat()
    violations = _publication_hold_violations(
        "censo_comunal",
        {
            "retained": True,
            "reason": "source_mode=fallback",
            "previous_generated_at_utc": "2026-10-15T00:00:00+00:00",
            "builds_held": 1,
            "since_utc": old,
        },
    )

    assert any("tope" in v for v in violations)


def test_held_days_tolerates_a_missing_marker():
    assert held_days({}) == float("inf")


# Para las pruebas de política basta un dataset estable: el verificador exige
# una entrada de metadata por cada nombre del registry.
POLICY_REGISTRY = REGISTRY[:1]


def _policy_metadata(hold):
    return {
        "datasets": {
            "censo_comunal": {
                "dataset": "censo_comunal",
                "source_mode": "fallback",
                "freshness": {"status": "stale"},
                "publication_hold": hold,
            }
        },
        "validations": {},
    }


def test_publication_policy_accepts_a_valid_hold():
    hold = {
        "retained": True,
        "reason": "source_mode=fallback",
        "previous_generated_at_utc": "2026-10-15T00:00:00+00:00",
        "builds_held": 2,
        "since_utc": datetime.now(UTC).isoformat(),
    }

    # No debe lanzar SystemExit.
    verify_publication_policy(
        metadata=_policy_metadata(hold),
        registry=POLICY_REGISTRY,
        manifest={"artifacts": []},
        changelog={"datasets": []},
    )


def test_publication_policy_still_rejects_fallback_without_hold():
    metadata = _policy_metadata(None)
    metadata["datasets"]["censo_comunal"]["publication_hold"] = None

    with pytest.raises(SystemExit):
        verify_publication_policy(
            metadata=metadata,
            registry=POLICY_REGISTRY,
            manifest={"artifacts": []},
            changelog={"datasets": []},
        )


def test_publication_policy_rejects_hold_beyond_the_cap():
    hold = {
        "retained": True,
        "reason": "source_mode=fallback",
        "previous_generated_at_utc": "2026-10-15T00:00:00+00:00",
        "builds_held": 1,
        "since_utc": (datetime.now(UTC) - timedelta(days=MAX_HELD_DAYS + 1)).isoformat(),
    }

    with pytest.raises(SystemExit):
        verify_publication_policy(
            metadata=_policy_metadata(hold),
            registry=POLICY_REGISTRY,
            manifest={"artifacts": []},
            changelog={"datasets": []},
        )
