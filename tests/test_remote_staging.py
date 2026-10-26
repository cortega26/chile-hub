"""Contrato del staging remoto (plan 153).

El espejo lo escribe una VM fuera de GitHub. Estos tests fijan las defensas que
impiden que un artefacto externo contamine `data/staging/`:

1. Solo se copian datasets de la allowlist.
2. Solo si quedaron en `live`/`monthly`: un fallback nunca pisa el dato bueno.
3. El `record_count` debe coincidir con las filas reales del CSV.
4. Un espejo incompleto se omite sin romper el pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.apply_remote_staging import (
    REMOTE_STAGING_DATASETS,
    apply_remote_staging,
)


def _seed(remote: Path, name: str, *, rows: int = 3, mode: str = "live", count: int | None = None):
    staging = remote / "data" / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    header = "codigo_comuna,nombre_comuna\n"
    body = "".join(f'"01{i:03d}",Comuna {i}\n' for i in range(rows))
    (staging / f"{name}.csv").write_text(header + body, encoding="utf-8")
    (staging / f"{name}.metadata.json").write_text(
        json.dumps(
            {
                "dataset": name,
                "source_mode": mode,
                "record_count": rows if count is None else count,
            }
        ),
        encoding="utf-8",
    )


def test_applies_a_live_dataset(tmp_path):
    remote, staging = tmp_path / "remote", tmp_path / "staging"
    staging.mkdir()
    _seed(remote, "pobreza_comunal")

    applied, skipped = apply_remote_staging(remote, staging)

    assert applied == ["pobreza_comunal"]
    # Los otros datasets de la allowlist no están en este espejo de prueba.
    assert all("pobreza_comunal" not in reason for reason in skipped)
    assert (staging / "pobreza_comunal.csv").is_file()
    assert (staging / "pobreza_comunal.metadata.json").is_file()


def test_never_overwrites_with_a_fallback(tmp_path):
    remote, staging = tmp_path / "remote", tmp_path / "staging"
    staging.mkdir()
    _seed(remote, "resultados_educacionales", mode="fallback")

    applied, skipped = apply_remote_staging(remote, staging)

    assert applied == []
    assert any("source_mode=fallback" in reason for reason in skipped)
    assert not (staging / "resultados_educacionales.csv").exists()


def test_ignores_a_dataset_outside_the_allowlist(tmp_path):
    remote, staging = tmp_path / "remote", tmp_path / "staging"
    staging.mkdir()
    _seed(remote, "empresas")

    applied, _ = apply_remote_staging(remote, staging)

    assert applied == []
    assert not (staging / "empresas.csv").exists()
    assert "empresas" not in REMOTE_STAGING_DATASETS


def test_rejects_a_record_count_mismatch(tmp_path):
    remote, staging = tmp_path / "remote", tmp_path / "staging"
    staging.mkdir()
    _seed(remote, "autoridades_electas", rows=3, count=99)

    applied, skipped = apply_remote_staging(remote, staging)

    assert applied == []
    assert any("record_count" in reason for reason in skipped)


def test_tolerates_an_incomplete_mirror(tmp_path):
    remote, staging = tmp_path / "remote", tmp_path / "staging"
    staging.mkdir()
    (remote / "data" / "staging").mkdir(parents=True)

    applied, skipped = apply_remote_staging(remote, staging)

    assert applied == []
    assert len(skipped) == len(REMOTE_STAGING_DATASETS)


def test_preserves_an_existing_good_file_when_the_mirror_is_worse(tmp_path):
    """El staging local no se toca si el espejo trae un fallback."""
    remote, staging = tmp_path / "remote", tmp_path / "staging"
    staging.mkdir()
    (staging / "pobreza_comunal.csv").write_text("codigo_comuna\n01101\n", encoding="utf-8")
    _seed(remote, "pobreza_comunal", mode="fallback")

    apply_remote_staging(remote, staging)

    assert (staging / "pobreza_comunal.csv").read_text(encoding="utf-8") == "codigo_comuna\n01101\n"
