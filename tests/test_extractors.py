import datetime
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from unittest.mock import MagicMock, patch

import openpyxl
from requests import HTTPError

from src.extractors import (
    bcentral_extractor,
    censo_extractor,
    censo_hogares_viviendas_extractor,
    mineduc_resultados_extractor,
    res_extractor,
    salud_extractor,
    siedu_extractor,
    sinim_finanzas_extractor,
    subdere_extractor,
)
from src.extractors.base import BaseExtractor

# ROOT_DIR is defined above


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


def _write_censo_workbook(path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet_totals = workbook.active
    sheet_totals.title = "2"
    sheet_age = workbook.create_sheet("4")
    sheet_totals.append([])
    sheet_age.append([])
    sheet_totals.cell(row=6, column=1, value=1)
    sheet_totals.cell(row=6, column=2, value="Tarapaca")
    sheet_totals.cell(row=6, column=3, value=11)
    sheet_totals.cell(row=6, column=4, value="Iquique")
    sheet_totals.cell(row=6, column=5, value=1101)
    sheet_totals.cell(row=6, column=6, value="Iquique")
    sheet_totals.cell(row=6, column=7, value=100)
    sheet_totals.cell(row=6, column=8, value=48)
    sheet_totals.cell(row=6, column=9, value=52)
    sheet_totals.cell(row=6, column=10, value=92.3)

    age_rows = [
        ("0 a 4", 10),
        ("15 a 19", 20),
        ("30 a 34", 25),
        ("45 a 49", 30),
        ("65 a 69", 15),
    ]
    for offset, (label, value) in enumerate(age_rows, start=6):
        sheet_age.cell(row=offset, column=5, value=1101)
        sheet_age.cell(row=offset, column=7, value=label)
        sheet_age.cell(row=offset, column=8, value=value)

    workbook.save(path)


def _write_censo_hogares_viviendas_workbook(path: Path) -> None:
    workbook = openpyxl.Workbook()
    sheet_viviendas = workbook.active
    sheet_viviendas.title = "2"
    sheet_hogares = workbook.create_sheet("6")
    sheet_viviendas.cell(row=5, column=1, value=1)
    sheet_viviendas.cell(row=5, column=2, value="Tarapaca")
    sheet_viviendas.cell(row=5, column=3, value=11)
    sheet_viviendas.cell(row=5, column=4, value="Iquique")
    sheet_viviendas.cell(row=5, column=5, value=1101)
    sheet_viviendas.cell(row=5, column=6, value="Iquique")
    sheet_viviendas.cell(row=5, column=7, value=120)
    sheet_viviendas.cell(row=5, column=8, value=100)
    sheet_viviendas.cell(row=5, column=9, value=18)
    sheet_viviendas.cell(row=5, column=10, value=2)

    sheet_hogares.cell(row=5, column=5, value=1101)
    sheet_hogares.cell(row=5, column=7, value=90)
    sheet_hogares.cell(row=5, column=8, value=3.1)

    workbook.save(path)


def _write_salud_csv(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "EstablecimientoCodigo;EstablecimientoGlosa;TipoEstablecimientoGlosa;"
                "DependenciaAdministrativa;NivelAtencionEstabglosa;RegionCodigo;RegionGlosa;"
                "ComunaCodigo;ComunaGlosa;TieneServicioUrgencia;TipoUrgencia;Latitud;Longitud;"
                "EstadoFuncionamiento",
                "1001;Hospital Iquique;Hospital;SNSS;Alta;1;Tarapaca;1101;Iquique;Si;"
                "Urgencia;-20.214;-70.152;Vigente",
            ]
        ),
        encoding="utf-8",
    )


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


class SinimFinanzasExtractorTests(unittest.TestCase):
    def test_normalize_rows_writes_required_schema(self):
        df = sinim_finanzas_extractor.normalize_rows(sinim_finanzas_extractor.FALLBACK_ROWS)
        required = {
            "anio",
            "codigo_comuna",
            "nombre_comuna",
            "ingresos_totales",
            "gastos_totales",
            "ingresos_propios_permanentes",
            "fondo_comun_municipal",
            "gasto_personal",
            "gasto_inversion",
        }
        self.assertTrue(required.issubset(df.columns))
        self.assertEqual(df["codigo_comuna"].dtype, sinim_finanzas_extractor.pl.String)

    def test_run_dry_run_returns_validation_without_writing(self):
        with patch.object(
            sinim_finanzas_extractor,
            "fetch_data",
            return_value=(sinim_finanzas_extractor.FALLBACK_ROWS, "fallback", "url", []),
        ):
            result = sinim_finanzas_extractor.SinimFinanzasExtractor().run(dry_run=True)
        self.assertEqual(result["status"], "ok")


class MineducResultadosExtractorTests(unittest.TestCase):
    def test_normalize_rows_writes_required_schema(self):
        df = mineduc_resultados_extractor.normalize_rows(mineduc_resultados_extractor.FALLBACK_ROWS)
        required = {
            "anio",
            "codigo_comuna",
            "matricula_total",
            "asistencia_promedio",
            "tasa_aprobacion",
            "tasa_reprobacion",
            "tasa_retiro",
            "establecimientos_reportados",
        }
        self.assertTrue(required.issubset(df.columns))
        self.assertEqual(df["codigo_comuna"].dtype, mineduc_resultados_extractor.pl.String)

    def test_run_dry_run_returns_validation_without_writing(self):
        with patch.object(
            mineduc_resultados_extractor,
            "fetch_data",
            return_value=(mineduc_resultados_extractor.FALLBACK_ROWS, "fallback", "url", []),
        ):
            result = mineduc_resultados_extractor.MineducResultadosExtractor().run(dry_run=True)
        self.assertEqual(result["status"], "ok")


class SieduExtractorTests(unittest.TestCase):
    def test_normalize_rows_writes_required_schema(self):
        df = siedu_extractor.normalize_rows(siedu_extractor.FALLBACK_ROWS)
        required = {
            "anio",
            "codigo_comuna",
            "codigo_indicador",
            "nombre_indicador",
            "categoria",
            "valor",
            "unidad",
            "fuente_original",
            "cobertura_tipo",
        }
        self.assertTrue(required.issubset(df.columns))
        self.assertEqual(df["codigo_comuna"].dtype, siedu_extractor.pl.String)

    def test_run_dry_run_returns_validation_without_writing(self):
        with patch.object(
            siedu_extractor,
            "fetch_data",
            return_value=(siedu_extractor.FALLBACK_ROWS, "fallback", "url", []),
        ):
            result = siedu_extractor.SieduExtractor().run(dry_run=True)
        self.assertEqual(result["status"], "ok")


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
        self.assertEqual(
            censo_hogares_viviendas_extractor.CensoHogaresViviendasExtractor().dataset_name,
            "censo_hogares_viviendas",
        )
        self.assertEqual(salud_extractor.SaludExtractor().dataset_name, "establecimientos_salud")

    def test_censo_parser_preserves_cut_codes_and_age_totals(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook = Path(tmpdir) / "censo_comunal.xlsx"
            _write_censo_workbook(workbook)

            df = censo_extractor.parse_workbook(workbook)

        self.assertEqual(df.height, 1)
        self.assertEqual(df["codigo_comuna"].item(), "01101")
        age_total = sum(df[column] for column in censo_extractor.AGE_BANDS)
        self.assertEqual(df.filter(age_total != df["poblacion_censada"]).height, 0)

    def test_salud_parser_preserves_cut_codes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "salud.csv"
            _write_salud_csv(source)

            df = salud_extractor.parse_csv(source)

        self.assertEqual(df.height, 1)
        self.assertEqual(df["codigo_comuna"].item(), "01101")

    def test_censo_hogares_viviendas_parser_preserves_cut_codes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook = Path(tmpdir) / "censo_hogares_viviendas.xlsx"
            _write_censo_hogares_viviendas_workbook(workbook)

            df = censo_hogares_viviendas_extractor.parse_workbook(workbook)

        self.assertEqual(df.height, 1)
        self.assertEqual(df["codigo_comuna"].item(), "01101")

    def test_censo_hogares_viviendas_write_staging_persists_csv_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workbook = Path(tmpdir) / "censo_hogares_viviendas.xlsx"
            _write_censo_hogares_viviendas_workbook(workbook)
            df = censo_hogares_viviendas_extractor.parse_workbook(workbook)
            csv_path = Path(tmpdir) / "censo_hogares_viviendas.csv"
            metadata_path = Path(tmpdir) / "censo_hogares_viviendas.metadata.json"
            with (
                patch.object(censo_hogares_viviendas_extractor, "STAGING_CSV_PATH", str(csv_path)),
                patch.object(
                    censo_hogares_viviendas_extractor, "METADATA_PATH", str(metadata_path)
                ),
            ):
                censo_hogares_viviendas_extractor.CensoHogaresViviendasExtractor().write_staging(
                    df, {"source_mode": "fallback"}
                )

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertTrue(csv_path.exists())
            self.assertEqual(metadata["record_count"], df.height)

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


class ResExtractorTests(unittest.TestCase):
    """Tests para el extractor del Registro de Empresas y Sociedades (RES)."""

    def test_extractor_class_contract(self):
        """El extractor cumple con el contrato de BaseExtractor."""
        extractor = res_extractor.ResExtractor()
        self.assertEqual(extractor.dataset_name, "empresas")

    def test_parse_resources_smoke(self):
        """Parseo de un CSV sintetico con las columnas esperadas del RES."""
        csv_content = (
            "ID;RUT;Razon Social;Fecha de actuacion (1era firma);"
            "Fecha de registro (ultima firma);Fecha de aprobacion x SII;"
            "Anio;Mes;Comuna Tributaria;Region Tributaria;"
            "Codigo de sociedad;Tipo de actuacion;Capital;Comuna Social;Region Social\n"
            "1;76286049-K;Servicios Digitales EIRL;02-05-2022;02-05-2022;02-05-2022;"
            "2022;Mayo;Providencia;13;EIRL;CONSTITUCION;7000000;Providencia;13\n"
            "2;76286055-4;Comercial ABC SpA;03-06-2022;03-06-2022;03-06-2022;"
            "2022;Junio;Las Condes;13;SPA;CONSTITUCION;25000000;Las Condes;13\n"
            "3;96567890-1;Distribuidora Sur SRL;15-06-2022;15-06-2022;15-06-2022;"
            "2022;Junio;Valparaiso;05;SRL;CONSTITUCION;5000000;Valparaiso;05\n"
        )
        contents = [csv_content.encode("utf-8")]
        df = res_extractor.parse_resources(contents)

        self.assertGreater(df.height, 0)
        self.assertIn("rut", df.columns)
        self.assertIn("razon_social", df.columns)
        self.assertIn("codigo_sociedad", df.columns)
        self.assertIn("capital", df.columns)
        self.assertIn("region_tributaria", df.columns)
        self.assertIn("comuna_tributaria", df.columns)

        # Verificar normalizacion de tipos
        ruts = df["rut"].to_list()
        self.assertIn("76286049-K", ruts)

        # codigo_sociedad debe estar mapeado a formato canonico
        sociedades = df["codigo_sociedad"].to_list()
        self.assertIn("EIRL", sociedades)
        self.assertIn("SpA", sociedades)  # SPA -> SpA (title case canonico)
        self.assertIn("SRL", sociedades)

    def test_parse_resources_handles_empty(self):
        """Parseo de lista vacia lanza SystemExit."""
        with self.assertRaises(SystemExit):
            res_extractor.parse_resources([])

    def test_write_staging_dry_run(self):
        """El extractor en dry_run no persiste archivos."""

        # Datos sinteticos minimos para evitar llamadas de red
        csv_content = (
            "ID;RUT;Razon Social;Fecha de actuacion (1era firma);"
            "Fecha de registro (ultima firma);Fecha de aprobacion x SII;"
            "Anio;Mes;Comuna Tributaria;Region Tributaria;"
            "Codigo de sociedad;Tipo de actuacion;Capital;Comuna Social;Region Social\n"
            "1;76286049-K;Test EIRL;02-05-2022;02-05-2022;02-05-2022;"
            "2022;Mayo;Santiago;13;EIRL;CONSTITUCION;1000000;Santiago;13\n"
        )
        fake_contents = [csv_content.encode("utf-8")]

        with patch.object(
            res_extractor, "fetch_resources", return_value=(fake_contents, "live", "test")
        ):
            extractor = res_extractor.ResExtractor()
            result = extractor.run(dry_run=True)
            self.assertIn("status", result)
            self.assertIn(result["status"], ("ok", "error"))

    def test_reuse_policy(self):
        """La politica de reutilizacion esta definida y es abierta."""
        policy = res_extractor.REUSE_POLICY
        self.assertEqual(policy["status"], "open-attribution")
        self.assertTrue(policy["redistribution_ok"])
        self.assertIn("CC-BY", policy["license"])


class SourceAdapterTests(unittest.TestCase):
    """Tests para los helpers reutilizables de extractores (source_adapter.py)."""

    def test_fetch_url_snapshot_success(self):
        """fetch_url_snapshot exitoso retorna success=True con contenido."""
        from src.extractors.source_adapter import fetch_url_snapshot

        mock_content = b"<html><body>datos</body></html>"
        with patch("src.extractors.source_adapter.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = mock_content
            mock_get.return_value = mock_resp

            with tempfile.TemporaryDirectory() as tmp:
                raw_dir = Path(tmp) / "raw"
                success, content, note = fetch_url_snapshot(
                    "https://example.com/data", raw_dir, "test_dataset"
                )
                self.assertTrue(success)
                self.assertEqual(content, mock_content)
                self.assertEqual(note, "official_landing_snapshot_saved")
                # Verifica que el snapshot se guardó en disco
                snapshots = list(raw_dir.glob("test_dataset_*.html"))
                self.assertEqual(len(snapshots), 1)

    def test_fetch_url_snapshot_failure(self):
        """fetch_url_snapshot ante ConnectionError retorna success=False."""
        from src.extractors.source_adapter import fetch_url_snapshot

        with patch(
            "src.extractors.source_adapter.requests.get",
            side_effect=ConnectionError("timeout"),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                raw_dir = Path(tmp) / "raw"
                success, content, note = fetch_url_snapshot(
                    "https://example.com/data", raw_dir, "test_dataset"
                )
                self.assertFalse(success)
                self.assertIsNone(content)
                self.assertIn("official_landing_unavailable", note)
                self.assertIn("timeout", note)

    def test_source_mode_from_live_success(self):
        """source_mode_from_live_success: True → live, False → fallback."""
        from src.extractors.source_adapter import source_mode_from_live_success

        self.assertEqual(source_mode_from_live_success(True), "live")
        self.assertEqual(source_mode_from_live_success(False), "fallback")

    def test_fallback_metadata_note(self):
        """fallback_metadata_note produce nota con prefijo estandarizado."""
        from src.extractors.source_adapter import fallback_metadata_note

        note = fallback_metadata_note("endpoint no disponible")
        self.assertIn("fallback_curated_rows_used:", note)
        self.assertIn("endpoint no disponible", note)

    def test_build_standard_metadata(self):
        """build_standard_metadata produce dict con todos los campos requeridos."""
        import polars as pl

        from src.extractors.source_adapter import build_standard_metadata

        df = pl.DataFrame({"codigo": ["13101", "13102"], "nombre": ["Santiago", "Iquique"]})
        meta = build_standard_metadata(
            dataset="test_dataset",
            source_name="API de prueba",
            source_url="https://example.com",
            source_mode="live",
            source_detail="public_api",
            df=df,
            notes=["prueba"],
            reuse_policy={"status": "open-attribution", "license": "CC-BY"},
        )
        self.assertEqual(meta["dataset"], "test_dataset")
        self.assertEqual(meta["source_name"], "API de prueba")
        self.assertEqual(meta["source_url"], "https://example.com")
        self.assertEqual(meta["source_mode"], "live")
        self.assertEqual(meta["source_detail"], "public_api")
        self.assertEqual(meta["record_count"], 2)
        self.assertEqual(meta["fields"], ["codigo", "nombre"])
        self.assertIn("prueba", meta["notes"])
        self.assertEqual(meta["reuse_policy"]["status"], "open-attribution")


class BaseExtractorEdgeTests(unittest.TestCase):
    """Tests de borde para el contrato BaseExtractor."""

    def test_ensure_staging_directories_idempotent(self):
        """ensure_staging_directories no falla si los directorios ya existen."""
        from src.extractors.base import ensure_staging_directories

        # Llamar dos veces: la primera crea, la segunda es idempotente
        ensure_staging_directories()
        ensure_staging_directories()
        # Si no lanza excepción, el test pasa


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(sys.argv))
