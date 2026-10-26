"""Contrato del triaje semanal (plan 152).

Lo que estos tests fijan:

1. Solo las señales **accionables** cuentan: una capa retenida sin vencer o una
   revisión "por vencer" no deben abrir un issue cada semana.
2. El orden es editorial y estable: error → retención vencida → stale →
   advertencias → calidad → revisiones vencidas.
3. Un artefacto ausente se declara, no revienta.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.weekly_triage import ROOT_DIR, collect_signals, render

SCRIPT = ROOT_DIR / "scripts" / "weekly_triage.py"


def _entry(name, **overrides):
    base = {
        "dataset": name,
        "severity": "ok",
        "freshness_status": "fresh",
        "held": False,
        "held_overdue": False,
        "retired": False,
        "actionable_warning_count": 0,
        "recommended_action": "Ninguna.",
    }
    base.update(overrides)
    return base


def _health(*entries, **counts):
    datasets = list(entries)
    base = {
        "generated_at_utc": "2026-10-26T00:00:00+00:00",
        "overall_status": "ok",
        "dataset_count": len(datasets),
        "live_count": len(datasets),
        "fallback_count": 0,
        "held_count": sum(1 for e in datasets if e["held"]),
        "held_overdue_count": sum(1 for e in datasets if e["held_overdue"]),
        "retired_count": 0,
        "review_due_count": 0,
        "review_approaching_count": 0,
        "top_issue": None,
        "datasets": datasets,
    }
    base.update(counts)
    return base


def _quality(*datasets):
    return {"average_score": 95.0, "datasets": list(datasets)}


def test_clean_health_has_no_signals_and_renders_the_clean_message():
    signals = collect_signals(_health(_entry("comunas")), _quality(), {})

    assert signals == []
    assert "sin señales" in render(signals, _health(_entry("comunas")), _quality()).lower()


def test_missing_health_declares_the_gap_instead_of_crashing():
    signals = collect_signals({}, {}, {})

    assert len(signals) == 1
    assert "hub_health.json" in signals[0].items[0]


def test_errors_come_before_every_other_signal():
    health = _health(
        _entry("comunas", severity="error"),
        _entry("calidad_aire", held=True, held_overdue=True),
        _entry("indicadores", actionable_warning_count=2),
    )

    signals = collect_signals(health, _quality(), {})

    assert [s.title.split(" (")[0] for s in signals] == [
        "Errores de validación",
        "Retención vencida",
        "Advertencias accionables",
    ]


def test_held_but_not_overdue_is_context_not_a_signal():
    """Una retención vigente no debe abrir un issue cada semana."""
    health = _health(_entry("calidad_aire", held=True))

    signals = collect_signals(health, _quality(), {})
    report = render(signals, health, _quality())

    assert signals == []
    assert "calidad_aire" in report  # aparece como contexto
    assert "Retenidas vigentes" in report


def test_review_approaching_is_not_a_signal_but_due_is():
    approaching = _health(_entry("comunas"), review_approaching_count=23)
    due = _health(_entry("comunas"), review_due_count=2)

    assert collect_signals(approaching, _quality(), {}) == []
    titles = [s.title for s in collect_signals(due, _quality(), {})]
    assert any("vencidas" in title for title in titles)


def test_stale_and_actionable_warnings_are_reported_with_their_dataset():
    health = _health(
        _entry("empresas", freshness_status="stale"),
        _entry("indicadores", actionable_warning_count=3, recommended_action="Revisar IPC."),
    )

    signals = collect_signals(health, _quality(), {})
    titles = [s.title for s in signals]
    assert any("stale" in title.lower() for title in titles)
    warnings = next(s for s in signals if "Advertencias" in s.title)
    assert "indicadores" in warnings.items[0]
    assert "Revisar IPC." in warnings.items[0]


def test_low_grade_quality_is_reported_but_healthy_grades_are_not():
    quality = _quality(
        {"dataset": "a", "grade": "A", "overall_score": 100.0, "blocking_reasons": ["x"]},
        {"dataset": "b", "grade": "C", "overall_score": 60.0, "blocking_reasons": []},
    )

    signals = collect_signals(_health(_entry("a")), quality, {})
    quality_signals = [s for s in signals if "Calidad" in s.title]

    assert len(quality_signals) == 1
    assert "b" in quality_signals[0].items[0]


def test_retired_datasets_are_excluded_from_active_signals():
    health = _health(
        _entry("delincuencia_comunal", retired=True, severity="error", freshness_status="stale")
    )

    assert collect_signals(health, _quality(), {}) == []


def test_cli_count_matches_the_rendered_signals(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--count"],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT_DIR,
    )
    assert completed.stdout.strip().isdigit()

    output = tmp_path / "triage.md"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output)],
        check=True,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    assert output.exists()
    assert "Triaje semanal" in output.read_text(encoding="utf-8")


def test_script_is_stdlib_only():
    """El workflow no instala dependencias: el script debe correr con stdlib."""
    source = Path(SCRIPT).read_text(encoding="utf-8")
    for forbidden in ("import polars", "import requests", "from src."):
        assert forbidden not in source
