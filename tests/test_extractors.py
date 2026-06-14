import datetime
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from requests import HTTPError

from src.extractors import (
    bcentral_extractor,
    censo_extractor,
    salud_extractor,
    subdere_extractor,
)
from src.extractors.base import BaseExtractor

ROOT_DIR = Path(__file__).resolve().parents[1]


class _MinimalExtractor(BaseExtractor):
    @property
    def dataset_name(self):
        return "test_dataset"

    def fetch(self, **kwargs):
        return {"records": [{"id": 1}]}

    def normalize(self, raw_data):
        return raw_data["records"]

    def validate(self, df, metadata):
        return {"valid": True, "record_count": len(df), "issues": []}

    def write_staging(self, df, metadata):
        raise AssertionError("write_staging no debe ejecutarse durante dry_run")


BCN_FIXTURE = {
    "features": [
        {
            "attributes": {
                "nom_reg": "Tarapaca",
                "nom_prov": "Iquique",
                "nom_com": "Iquique",
                "cod_comuna": 1101,
                "codregion": 1,
            }
        },
        {
            "attributes": {
                "nom_reg": "Tarapaca",
                "nom_prov": "Iquique",
                "nom_com": "Alto Hospicio",
                "cod_comuna": 1107,
                "codregion": 1,
            }
        },
    ]
}


def mock_response(payload, status_code=200):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload
    if status_code >= 400:
        response.raise_for_status.side_effect = HTTPError(f"HTTP {status_code}")
    return response


class SubdereExtractorTests(unittest.TestCase):
    def test_fetch_bcn_comunas_normalizes_codes_and_saves_snapshot(self):
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch.object(subdere_extractor, "RAW_DIR", tmpdir),
            patch.object(
                subdere_extractor,
                "_stealth_get",
                return_value=mock_response(BCN_FIXTURE),
            ),
        ):
            df, skipped, deduped, supplemental = subdere_extractor.fetch_bcn_comunas()

            self.assertEqual(df.filter(df["codigo_comuna"] == "01101").height, 1)
            self.assertEqual(skipped, 0)
            self.assertEqual(deduped, 0)
            self.assertGreaterEqual(supplemental, 1)
            self.assertEqual(len(list(Path(tmpdir).glob("bcn_comunas_*.json"))), 1)

    def test_fetch_bcn_comunas_raises_on_http_error(self):
        with (
            patch.object(subdere_extractor, "_stealth_get", return_value=mock_response({}, 503)),
            self.assertRaises(HTTPError),
        ):
            subdere_extractor.fetch_bcn_comunas()

    def test_normalize_dpa_writes_required_columns(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = str(Path(tmpdir) / "comunas.metadata.json")
            with (
                patch.object(subdere_extractor, "STAGING_DIR", tmpdir),
                patch.object(subdere_extractor, "METADATA_PATH", metadata_path),
                patch.object(subdere_extractor, "fetch_bcn_comunas") as fetch,
            ):
                fetch.return_value = (
                    subdere_extractor.pl.DataFrame(subdere_extractor.DPA_FALLBACK_DATA[:2]),
                    0,
                    0,
                    0,
                )
                output_path = subdere_extractor.normalize_dpa()

            df = subdere_extractor.pl.read_csv(
                output_path,
                schema_overrides={
                    "codigo_region": subdere_extractor.pl.String,
                    "codigo_provincia": subdere_extractor.pl.String,
                    "codigo_comuna": subdere_extractor.pl.String,
                },
            )
            required = {
                "codigo_comuna",
                "nombre_comuna",
                "nombre_comuna_clean",
                "codigo_provincia",
                "nombre_provincia",
                "codigo_region",
                "nombre_region",
                "latitud_cabecera",
                "longitud_cabecera",
                "poblacion_estimada",
            }
            self.assertTrue(required.issubset(df.columns))
            self.assertEqual(df["codigo_comuna"].dtype, subdere_extractor.pl.String)


class BCentralExtractorTests(unittest.TestCase):
    def _payload(self, codigo="uf", year=2026, count=3):
        return {
            "codigo": codigo,
            "serie": [
                {
                    "fecha": datetime.date(year, 1, index + 1).isoformat() + "T00:00:00.000Z",
                    "valor": 39000.0 + index,
                }
                for index in range(count)
            ],
        }

    def test_fetch_indicator_year_parses_records_and_saves_snapshot(self):
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch.object(bcentral_extractor, "RAW_DIR", tmpdir),
            patch.object(
                bcentral_extractor.requests,
                "get",
                return_value=mock_response(self._payload()),
            ),
        ):
            records = bcentral_extractor.fetch_indicator_year("uf", 2026)

            self.assertEqual(len(records), 3)
            self.assertEqual(records[0]["codigo_indicador"], "uf")
            self.assertEqual(len(list(Path(tmpdir).glob("mindicador_uf_2026_*.json"))), 1)

    def test_fetch_indicator_year_raises_on_http_error(self):
        with (
            patch.object(bcentral_extractor.requests, "get", return_value=mock_response({}, 503)),
            self.assertRaises(HTTPError),
        ):
            bcentral_extractor.fetch_indicator_year("uf", 2026)

    def test_fetch_all_history_continues_after_one_indicator_fails(self):
        current_year = datetime.date.today().year

        def fetch(codigo, year):
            if codigo == "uf":
                raise HTTPError("503")
            return [{"fecha": f"{year}-01-01", "codigo_indicador": codigo, "valor": 1.0}]

        with (
            patch.object(
                bcentral_extractor,
                "load_existing_staging",
                return_value=(None, None, []),
            ),
            patch.object(bcentral_extractor, "HISTORY_START_YEAR", current_year),
            patch.object(bcentral_extractor, "fetch_indicator_year", side_effect=fetch),
            patch.object(bcentral_extractor, "load_latest_raw_snapshot", return_value=[]),
            patch.object(bcentral_extractor.time, "sleep"),
        ):
            df, diagnostics = bcentral_extractor.fetch_all_history()

        self.assertIsNotNone(df)
        self.assertTrue(any(item.startswith("uf/") for item in diagnostics["fetch_failures"]))
        self.assertNotIn("uf", set(df["codigo_indicador"].unique()))
        self.assertEqual(set(df["codigo_indicador"].unique()), {"dolar", "euro", "utm", "ipc"})


class BaseExtractorContractTests(unittest.TestCase):
    def test_base_class_is_abstract(self):
        with self.assertRaises(TypeError):
            BaseExtractor()

    def test_run_dry_run_returns_validation_without_writing(self):
        result = _MinimalExtractor().run(dry_run=True)
        self.assertTrue(result["valid"])
        self.assertEqual(result["record_count"], 1)

    def test_concrete_extractors_publish_dataset_names(self):
        self.assertEqual(subdere_extractor.SubdereExtractor().dataset_name, "comunas")
        self.assertEqual(bcentral_extractor.BCentralExtractor().dataset_name, "indicadores")
        self.assertEqual(censo_extractor.CensoExtractor().dataset_name, "censo_comunal")
        self.assertEqual(salud_extractor.SaludExtractor().dataset_name, "establecimientos_salud")

    def test_censo_parser_preserves_cut_codes_and_age_totals(self):
        workbook = sorted((ROOT_DIR / "data" / "raw").glob("ine_censo2024_comunal_*.xlsx"))[-1]
        df = censo_extractor.parse_workbook(workbook)
        self.assertEqual(df.height, 346)
        self.assertEqual(df["codigo_comuna"].str.len_chars().min(), 5)
        age_total = sum(df[column] for column in censo_extractor.AGE_BANDS)
        self.assertEqual(df.filter(age_total != df["poblacion_censada"]).height, 0)

    def test_salud_parser_preserves_cut_codes(self):
        source = sorted((ROOT_DIR / "data" / "raw").glob("minsal_establecimientos_salud_*.csv"))[-1]
        df = salud_extractor.parse_csv(source)
        self.assertGreater(df.height, 5000)
        self.assertEqual(df["codigo_comuna"].str.len_chars().min(), 5)

    def test_concrete_write_staging_persists_csv_and_metadata(self):
        df = bcentral_extractor.generate_fallback_indicators()
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "indicadores.csv"
            metadata_path = Path(tmpdir) / "indicadores.metadata.json"
            with (
                patch.object(bcentral_extractor, "STAGING_CSV_PATH", str(csv_path)),
                patch.object(bcentral_extractor, "METADATA_PATH", str(metadata_path)),
            ):
                bcentral_extractor.BCentralExtractor().write_staging(
                    df, {"source_mode": "fallback"}
                )

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertTrue(csv_path.exists())
            self.assertEqual(metadata["dataset"], "indicadores")
            self.assertEqual(metadata["record_count"], df.height)


if __name__ == "__main__":
    unittest.main()
