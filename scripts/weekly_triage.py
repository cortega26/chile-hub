"""Triaje semanal de señales del hub (plan 152).

Lee los artefactos publicados y produce un informe Markdown con las señales
accionables ordenadas por impacto. No inventa estado: si un artefacto falta, lo
declara y sigue.

Uso:

    python scripts/weekly_triage.py                  # Markdown a stdout
    python scripts/weekly_triage.py --output f.md    # Markdown a archivo
    python scripts/weekly_triage.py --count          # número de señales

El workflow `weekly-triage.yml` publica el informe como un único issue
actualizable, para que la agenda operativa no dependa de que alguien mire los
reportes a mano.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"

MAX_ITEMS = 6


@dataclass
class Signal:
    """Un bloque del informe, ya ordenado por quien lo construye."""

    title: str
    items: list[str] = field(default_factory=list)
    note: str | None = None


def _load(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _active(health: dict) -> list[dict]:
    return [
        entry
        for entry in health.get("datasets", [])
        if not entry.get("retired") and not entry.get("held")
    ]


def collect_signals(health: dict, quality: dict, readiness: dict) -> list[Signal]:
    """Devuelve las señales no vacías, en orden de impacto.

    El orden es una decisión editorial, no un score inventado:

    1. `error` — dato publicado que no pasa su validación.
    2. Retención vencida — tiene fecha límite y ya pasó.
    3. Datos `stale` — el consumidor está recibiendo algo viejo.
    4. Advertencias accionables — requieren mirada humana.
    5. Retención vigente — informativo, sin fecha vencida.
    6. Calidad — grados C/D del scorecard.
    7. Revisiones de registro — agenda de gobernanza, no urgencia.
    """
    if not health:
        return [Signal("Sin datos de salud", ["`hub_health.json` no está disponible."])]

    signals: list[Signal] = []
    active = _active(health)

    errors = sorted(entry["dataset"] for entry in active if entry.get("severity") == "error")
    if errors:
        signals.append(
            Signal(
                f"Errores de validación ({len(errors)})",
                [f"`{name}`" for name in errors],
                "Un dato con error no debería consumirse. Revisar `dataset_status.json`.",
            )
        )

    overdue = sorted(
        entry["dataset"] for entry in health.get("datasets", []) if entry.get("held_overdue")
    )
    if overdue:
        signals.append(
            Signal(
                f"Retención vencida ({len(overdue)})",
                [f"`{name}`" for name in overdue],
                "Superaron el tope de retención. Ver el issue con label `data-hold`: "
                "reparar la fuente, sacar la capa del carril o retirarla.",
            )
        )

    stale = sorted(entry["dataset"] for entry in active if entry.get("freshness_status") == "stale")
    if stale:
        signals.append(Signal(f"Datos stale ({len(stale)})", [f"`{name}`" for name in stale]))

    warned = sorted(
        (
            (
                entry.get("actionable_warning_count", 0),
                entry["dataset"],
                entry.get("recommended_action"),
            )
            for entry in active
            if entry.get("actionable_warning_count", 0) > 0
        ),
        reverse=True,
    )
    if warned:
        items = [
            f"`{name}` — {count} advertencia(s): {action or 'sin acción sugerida'}"
            for count, name, action in warned[:MAX_ITEMS]
        ]
        if len(warned) > MAX_ITEMS:
            items.append(f"… y {len(warned) - MAX_ITEMS} capa(s) más.")
        signals.append(
            Signal(
                f"Advertencias accionables ({len(warned)})",
                items,
                "`chile-hub health` da el detalle.",
            )
        )

    # `blocking_reasons` del scorecard no significa "bloqueante": son las
    # deducciones explicadas (p. ej. "Cobertura not_applicable"). El grado es la
    # señal; usarlo evita marcar 13 capas sanas como problema.
    low_grade = sorted(
        (entry.get("overall_score", 0.0), entry["dataset"], entry.get("grade", "?"))
        for entry in quality.get("datasets", [])
        if entry.get("grade") in {"C", "D"}
    )
    if low_grade:
        items = [
            f"`{name}` — grado {grade}, score {score:.0f}"
            for score, name, grade in low_grade[:MAX_ITEMS]
        ]
        signals.append(
            Signal(
                f"Calidad bajo umbral ({len(low_grade)})",
                items,
                "`dataset_quality.md` da el desglose.",
            )
        )

    # Solo revisiones VENCIDAS. Las "por vencer" (<90 d) son una ventana de tres
    # meses: repetirlas cada semana convertiría el triaje en ruido.
    due = health.get("review_due_count", 0)
    if due:
        signals.append(
            Signal(
                f"Revisiones de registro vencidas ({due})",
                [],
                "`data/source_registry.json` (`review_by`) y `docs/dataset-inclusion-criteria.md`.",
            )
        )

    return signals


def render(signals: list[Signal], health: dict, quality: dict) -> str:
    if not signals:
        lines = [
            "## Triaje semanal — sin señales",
            "",
            "Ninguna señal accionable en los artefactos publicados.",
            "",
        ]
    else:
        lines = [
            f"## Triaje semanal — {len(signals)} señal(es)",
            "",
        ]
        for index, signal in enumerate(signals, 1):
            lines.append(f"### {index}. {signal.title}")
            lines.append("")
            lines.extend(f"- {item}" for item in signal.items)
            if signal.note:
                lines.append("")
                lines.append(f"> {signal.note}")
            lines.append("")

    held_names = sorted(
        entry["dataset"] for entry in health.get("datasets", []) if entry.get("held")
    )
    if held_names:
        lines.extend(["**Retenidas vigentes** (no accionable hasta vencer):", ""])
        lines.extend(f"- `{name}`" for name in held_names)
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "**Contexto del build**",
            "",
            f"- Generado: `{health.get('generated_at_utc', 'desconocido')}`",
            f"- Estado general: `{health.get('overall_status', 'desconocido')}`",
            f"- Capas: {health.get('dataset_count', '?')} "
            f"(live {health.get('live_count', '?')} · fallback {health.get('fallback_count', '?')} · "
            f"retenidas {health.get('held_count', '?')} · retiradas {health.get('retired_count', '?')})",
            f"- Calidad promedio: {quality.get('average_score', 'sin dato')}",
            f"- Top issue: `{(health.get('top_issue') or {}).get('dataset', 'ninguno')}`",
            "",
            "_Generado por `scripts/weekly_triage.py`. No modifica datos ni código: "
            "solo ordena la agenda._",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--normalized-dir", default=str(NORMALIZED_DIR))
    parser.add_argument("--output", default=None, help="Archivo destino (default: stdout)")
    parser.add_argument("--count", action="store_true", help="Imprime solo el número de señales")
    args = parser.parse_args(argv)

    normalized = Path(args.normalized_dir)
    health = _load(normalized / "hub_health.json")
    quality = _load(normalized / "dataset_quality.json")
    readiness = _load(normalized / "source_readiness.json")

    signals = collect_signals(health, quality, readiness)
    if args.count:
        print(len(signals))
        return 0

    report = render(signals, health, quality)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"triage: {len(signals)} señal(es) → {args.output}")
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
