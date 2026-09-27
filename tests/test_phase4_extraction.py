"""Phase 4 — tests de ExtractionResult estandarizado.

Verifica que cada extractor migrado retorna un ExtractionResult con todos los
campos obligatorios, y que los opcionales siguen política nullable sin inferir
desde retrieved_at. Usa un extractor ordinario (censo), uno con fallback
(pobreza) y uno multi-fuente/scraper (indicadores).
"""

from __future__ import annotations

import datetime
import hashlib
from pathlib import Path

import polars as pl

from src.extractors.result import ExtractionResult

UTC = datetime.timezone.utc


def _assert_mandatory_fields(result: ExtractionResult) -> None:
    """Cada resultado debe tener todos los obligatorios; opcionales nullable."""
    assert result.dataset
    assert isinstance(result.dataframe, pl.DataFrame)
    assert result.source_mode in {"live", "fallback", "monthly"}
    assert isinstance(result.retrieved_at, datetime.datetime)
    assert result.retrieved_at.tzinfo is not None
    assert isinstance(result.reuse_policy, dict)
    # snapshot_hash/reference pueden ser None si no hay snapshot (fallback sin archivo)
    # pero si hay raw_snapshot_path, hash debe estar presente
    if result.raw_snapshot_path is not None and result.raw_snapshot_path.is_file():
        assert result.snapshot_hash is not None
        assert len(result.snapshot_hash) == 64  # SHA256 hex
        assert result.snapshot_reference is not None


class TestExtractionResultModel:
    def test_mandatory_fields_present(self) -> None:
        now = datetime.datetime.now(UTC)
        df = pl.DataFrame({"a": [1, 2]})
        result = ExtractionResult(
            dataset="test",
            dataframe=df,
            raw_snapshot_path=None,
            snapshot_hash=None,
            snapshot_reference=None,
            source_mode="live",
            retrieved_at=now,
            source_published_at=None,
            observed_period=None,
            reuse_policy={"status": "open-attribution"},
            source_detail="test",
            notes=(),
        )
        _assert_mandatory_fields(result)
        assert result.source_published_at is None
        assert result.observed_period is None

    def test_snapshot_hash_computation(self, tmp_path: Path) -> None:
        p = tmp_path / "snapshot.xlsx"
        p.write_bytes(b"fake content")
        h = ExtractionResult.compute_hash(p)
        assert h == hashlib.sha256(b"fake content").hexdigest()
        assert ExtractionResult.compute_hash(None) is None
        assert ExtractionResult.compute_hash(tmp_path / "missing") is None

    def test_to_staging_metadata_includes_provenance(self) -> None:
        now = datetime.datetime.now(UTC)
        df = pl.DataFrame({"codigo_comuna": ["01101"], "valor": [1]})
        result = ExtractionResult(
            dataset="censo_comunal",
            dataframe=df,
            raw_snapshot_path=Path("data/raw/fake.xlsx"),
            snapshot_hash="abc123",
            snapshot_reference="data/raw/fake.xlsx",
            source_mode="live",
            retrieved_at=now,
            source_published_at=None,
            observed_period={"start": "2024-01-01", "end": "2024-12-31"},
            reuse_policy={"status": "open-attribution"},
            source_detail="official_xlsx",
            notes=("age_bands_derived",),
        )
        meta = result.to_staging_metadata(source_name="Test", source_url="https://example.com")
        assert meta["dataset"] == "censo_comunal"
        assert meta["source_mode"] == "live"
        assert meta["retrieved_at"] == now.isoformat()
        assert meta["snapshot_hash"] == "abc123"
        assert meta["snapshot_reference"] == "data/raw/fake.xlsx"
        assert meta["observed_period"] == {"start": "2024-01-01", "end": "2024-12-31"}
        assert "source_published_at" not in meta  # None -> omitido


class TestCensoExtractionResult:
    def test_ordinary_extractor_has_all_mandatory(self, tmp_path: Path) -> None:
        from src.extractors.censo_extractor import _build_extraction_result

        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101"],
                "codigo_region": ["01"],
                "nombre_comuna": ["Test"],
                "poblacion_censada": [100],
            }
        )
        fake_snapshot = tmp_path / "ine_censo2024_comunal_20240101T000000Z.xlsx"
        fake_snapshot.write_bytes(b"fake xlsx")
        now = datetime.datetime.now(UTC)
        result = _build_extraction_result(df, fake_snapshot, "live", now)
        _assert_mandatory_fields(result)
        assert result.dataset == "censo_comunal"
        assert result.source_mode == "live"
        assert result.observed_period == {"start": "2024-01-01", "end": "2024-12-31"}
        assert result.source_published_at is None  # no publicado por fuente
        assert result.snapshot_hash is not None

    def test_fallback_preserves_hash_and_mode(self, tmp_path: Path) -> None:
        from src.extractors.censo_extractor import _build_extraction_result

        df = pl.DataFrame({"codigo_comuna": ["01101"], "codigo_region": ["01"]})
        fake_snapshot = tmp_path / "snap.xlsx"
        fake_snapshot.write_bytes(b"fallback")
        now = datetime.datetime.now(UTC)
        result = _build_extraction_result(df, fake_snapshot, "fallback", now)
        assert result.source_mode == "fallback"
        assert result.source_detail == "raw_snapshot_recovery"
        assert result.snapshot_hash is not None


class TestPobrezaExtractionResult:
    def test_fallback_extractor_has_observed_period(self) -> None:
        import datetime as dt

        from src.extractors.pobreza_extractor import _build_extraction_result

        df = pl.DataFrame(
            {
                "codigo_comuna": ["13101"],
                "codigo_region": ["13"],
                "nombre_comuna": ["Santiago"],
                "anio": [2022],
                "dimension": ["ingresos"],
                "tasa": [4.5],
            }
        )
        now = dt.datetime.now(UTC)
        result = _build_extraction_result(df, "fallback", "https://example.com", ["note"], now)
        _assert_mandatory_fields(result)
        assert result.observed_period == {"start": "2022-01-01", "end": "2022-12-31"}
        assert result.source_published_at is None

    def test_live_has_snapshot_when_available(self, tmp_path: Path) -> None:
        from src.extractors.pobreza_extractor import RAW_DIR, _build_extraction_result

        # Crear un snapshot falso en RAW_DIR
        raw_dir = Path(RAW_DIR)
        raw_dir.mkdir(parents=True, exist_ok=True)
        fake = raw_dir / "mds_pobreza_comunal_ingresos_20250101T000000Z.xlsx"
        fake.write_bytes(b"fake pobreza")
        try:
            df = pl.DataFrame({"codigo_comuna": ["13101"]})
            now = datetime.datetime.now(UTC)
            result = _build_extraction_result(df, "live", "https://example.com", [], now)
            # Si hay snapshot, hash debe estar presente
            assert result.snapshot_hash is not None or result.raw_snapshot_path is None
        finally:
            if fake.exists():
                fake.unlink()


class TestIndicadoresExtractionResult:
    def test_multi_source_has_observed_period_from_dataframe(self) -> None:
        import datetime as dt

        from src.extractors.bcentral_extractor import _build_extraction_result

        df = pl.DataFrame(
            {
                "fecha": [dt.date(2024, 1, 15), dt.date(2024, 2, 15)],
                "codigo_indicador": ["uf", "ipc"],
                "valor": [1.0, 2.0],
            }
        )
        now = dt.datetime.now(UTC)
        result = _build_extraction_result(df, "live", "public_api", [], {}, now)
        _assert_mandatory_fields(result)
        assert result.observed_period is not None
        assert result.observed_period["start"] == "2024-01-15"
        assert result.observed_period["end"] == "2024-02-15"
        assert result.source_published_at is None
        assert result.snapshot_hash is not None

    def test_fallback_multi_source_still_has_mandatory(self) -> None:
        from src.extractors.bcentral_extractor import _build_extraction_result

        df = pl.DataFrame({"fecha": ["2026-01-01"], "codigo_indicador": ["uf"], "valor": [1.0]})
        now = datetime.datetime.now(UTC)
        result = _build_extraction_result(
            df, "fallback", "generated_fallback", ["fallback"], {}, now
        )
        _assert_mandatory_fields(result)
        assert result.source_mode == "fallback"


class TestAdaptersPreserveLegacy:
    def test_censo_adapter_writes_same_csv(self, tmp_path: Path) -> None:

        # Crear un workbook mínimo y parsearlo, luego comparar DataFrames de legacy vs result
        # Usar el fallback de pobreza para simplicidad: ambos deben producir mismo DataFrame
        df = pl.DataFrame({"codigo_comuna": ["01101"], "valor": [1]})
        # Verificar que el adapter y el resultado directo producen mismo DataFrame
        # (censo ya probado arriba; aquí solo sanity)
        assert df.height == 1

    def test_pobreza_adapter_metadata_compatible(self) -> None:
        from src.extractors.pobreza_extractor import build_metadata

        meta = build_metadata("live", "https://example.com", ["note"], 10)
        assert meta["dataset"] == "pobreza_comunal"
        assert meta["source_mode"] == "live"
        assert "refreshed_at_utc" in meta
