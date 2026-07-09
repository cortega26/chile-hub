"""Tests unitarios para las funciones de validación en src/validation.py.

Cada validador se prueba con casos mínimos: datos correctos, errores
esperados y condiciones de borde.  Estos tests complementan los tests
de integración en test_chile_hub.py y test_pipeline_logic.py.
"""

import sys
import unittest
from pathlib import Path

import polars as pl

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.validation import (
    validate_autoridades_electas,
    validate_censo_comunal,
    validate_censo_hogares_viviendas,
    validate_comunas,
    validate_consumo_electrico_comunal,
    validate_distritos_electorales,
    validate_empresas,
    validate_establecimientos_educacionales,
    validate_establecimientos_salud,
    validate_indicadores,
    validate_partidos_politicos,
    validate_pobreza_comunal,
    validate_provincias,
    validate_puntos_interes,
    validate_regiones,
)

# ── Fixtures mínimos ──────────────────────────────────────────────────────────

VALID_COMMUNE_CODES = [f"{i:05d}" for i in range(1, 347)]  # "00001".."00346"


def _make_comunas_df(rows, *, source_mode="live"):
    """DataFrame mínimo de comunas con las columnas que espera el validador."""
    return pl.DataFrame(
        rows,
        schema={
            "codigo_comuna": pl.String,
            "codigo_region": pl.String,
            "codigo_provincia": pl.String,
            "nombre_comuna": pl.String,
        },
    )


# ── validate_regiones ─────────────────────────────────────────────────────────


class ValidateRegionesTests(unittest.TestCase):
    def test_ok_minimal(self):
        df = pl.DataFrame({"codigo_region": ["01", "02", "03"]})
        result = validate_regiones(df)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["record_count"], 3)

    def test_empty_dataset_is_error(self):
        df = pl.DataFrame({"codigo_region": []}, schema={"codigo_region": pl.String})
        result = validate_regiones(df)
        self.assertEqual(result["status"], "error")
        self.assertIn("empty", result["errors"][0])

    def test_duplicate_codes_error(self):
        df = pl.DataFrame({"codigo_region": ["01", "01", "02"]})
        result = validate_regiones(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("duplicate" in e for e in result["errors"]))


# ── validate_provincias ───────────────────────────────────────────────────────


class ValidateProvinciasTests(unittest.TestCase):
    def test_ok_minimal(self):
        df = pl.DataFrame(
            {
                "codigo_region": ["01", "01"],
                "codigo_provincia": ["011", "012"],
            }
        )
        result = validate_provincias(df)
        self.assertEqual(result["status"], "ok")

    def test_empty_dataset_is_error(self):
        df = pl.DataFrame(
            {"codigo_region": [], "codigo_provincia": []},
            schema={"codigo_region": pl.String, "codigo_provincia": pl.String},
        )
        result = validate_provincias(df)
        self.assertEqual(result["status"], "error")

    def test_duplicate_region_province_pair_error(self):
        df = pl.DataFrame(
            {
                "codigo_region": ["01", "01"],
                "codigo_provincia": ["011", "011"],
            }
        )
        result = validate_provincias(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("unique" in e for e in result["errors"]))


# ── validate_comunas ──────────────────────────────────────────────────────────


class ValidateComunasTests(unittest.TestCase):
    def test_ok_live_with_346_communes(self):
        rows = [
            {
                "codigo_comuna": f"{i:05d}",
                "codigo_region": f"{i // 10000:02d}",
                "codigo_provincia": f"{i // 1000:03d}",
                "nombre_comuna": f"Comuna {i}",
            }
            for i in range(1, 347)
        ]
        df = _make_comunas_df(rows, source_mode="live")
        result = validate_comunas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["record_count"], 346)

    def test_duplicate_comuna_code_error(self):
        df = _make_comunas_df(
            [
                {
                    "codigo_comuna": "01101",
                    "codigo_region": "01",
                    "codigo_provincia": "011",
                    "nombre_comuna": "Iquique",
                },
                {
                    "codigo_comuna": "01101",
                    "codigo_region": "01",
                    "codigo_provincia": "011",
                    "nombre_comuna": "Duplicada",
                },
            ]
        )
        result = validate_comunas(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("duplicate" in e for e in result["errors"]))

    def test_live_mode_with_too_few_rows_error(self):
        df = _make_comunas_df(
            [
                {
                    "codigo_comuna": "01101",
                    "codigo_region": "01",
                    "codigo_provincia": "011",
                    "nombre_comuna": "Sola",
                }
            ],
            source_mode="live",
        )
        result = validate_comunas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("incomplete" in e for e in result["errors"]))

    def test_fallback_mode_warns_on_unexpected_row_count(self):
        rows = [
            {
                "codigo_comuna": f"{i:05d}",
                "codigo_region": "01",
                "codigo_provincia": "011",
                "nombre_comuna": f"C{i}",
            }
            for i in range(1, 50)
        ]
        df = _make_comunas_df(rows)
        result = validate_comunas(df, {"source_mode": "fallback"})
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["warnings"])

    def test_fallback_mode_adds_coverage_warning(self):
        rows = [
            {
                "codigo_comuna": f"{i:05d}",
                "codigo_region": "01",
                "codigo_provincia": "011",
                "nombre_comuna": f"FB{i}",
            }
            for i in range(1, 19)  # Exactly FALLBACK_COMUNAS_COUNT (18)
        ]
        df = _make_comunas_df(rows)
        result = validate_comunas(df, {"source_mode": "fallback"})
        self.assertEqual(result["status"], "ok")
        self.assertTrue(any("limited" in w for w in result["warnings"]))


# ── validate_censo_comunal ────────────────────────────────────────────────────


class ValidateCensoComunalTests(unittest.TestCase):
    def _make_censo(self, rows):
        schema = {
            "codigo_comuna": pl.String,
            "poblacion_censada": pl.Int64,
            "poblacion_0_14": pl.Int64,
            "poblacion_15_29": pl.Int64,
            "poblacion_30_44": pl.Int64,
            "poblacion_45_64": pl.Int64,
            "poblacion_65_mas": pl.Int64,
        }
        return pl.DataFrame(rows, schema=schema)

    def test_ok_for_346_communes(self):
        rows = [
            {
                "codigo_comuna": f"{i:05d}",
                "poblacion_censada": 1000,
                "poblacion_0_14": 200,
                "poblacion_15_29": 200,
                "poblacion_30_44": 200,
                "poblacion_45_64": 200,
                "poblacion_65_mas": 200,
            }
            for i in range(1, 347)
        ]
        df = self._make_censo(rows)
        result = validate_censo_comunal(df, None)
        self.assertEqual(result["status"], "ok")

    def test_empty_dataset_error(self):
        df = pl.DataFrame(
            {
                "codigo_comuna": [],
                "poblacion_censada": [],
                "poblacion_0_14": [],
                "poblacion_15_29": [],
                "poblacion_30_44": [],
                "poblacion_45_64": [],
                "poblacion_65_mas": [],
            },
            schema={
                "codigo_comuna": pl.String,
                "poblacion_censada": pl.Int64,
                "poblacion_0_14": pl.Int64,
                "poblacion_15_29": pl.Int64,
                "poblacion_30_44": pl.Int64,
                "poblacion_45_64": pl.Int64,
                "poblacion_65_mas": pl.Int64,
            },
        )
        result = validate_censo_comunal(df, None)
        self.assertEqual(result["status"], "error")

    def test_wrong_row_count_error(self):
        df = self._make_censo(
            [
                {
                    "codigo_comuna": "01101",
                    "poblacion_censada": 100,
                    "poblacion_0_14": 50,
                    "poblacion_15_29": 50,
                    "poblacion_30_44": 0,
                    "poblacion_45_64": 0,
                    "poblacion_65_mas": 0,
                }
            ]
        )
        result = validate_censo_comunal(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("346" in e for e in result["errors"]))

    def test_duplicate_comuna_code_error(self):
        rows = [
            {
                "codigo_comuna": "01101",
                "poblacion_censada": 100,
                "poblacion_0_14": 50,
                "poblacion_15_29": 50,
                "poblacion_30_44": 0,
                "poblacion_45_64": 0,
                "poblacion_65_mas": 0,
            },
        ] * 346
        df = self._make_censo(rows)
        result = validate_censo_comunal(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("unique" in e for e in result["errors"]))

    def test_age_bands_must_sum_to_total(self):
        df = self._make_censo(
            [
                {
                    "codigo_comuna": f"{i:05d}",
                    "poblacion_censada": 1000,
                    "poblacion_0_14": 100,
                    "poblacion_15_29": 100,
                    "poblacion_30_44": 100,
                    "poblacion_45_64": 100,
                    "poblacion_65_mas": 100,  # suma 500 ≠ 1000
                }
                for i in range(1, 347)
            ]
        )
        result = validate_censo_comunal(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("sum" in e for e in result["errors"]))


# ── validate_censo_hogares_viviendas ──────────────────────────────────────────


class ValidateCensoHogaresViviendasTests(unittest.TestCase):
    def _make_df(self, rows):
        schema = {
            "codigo_comuna": pl.String,
            "viviendas_censadas": pl.Int64,
            "viviendas_particulares_ocupadas": pl.Int64,
            "viviendas_particulares_desocupadas": pl.Int64,
            "viviendas_colectivas": pl.Int64,
            "hogares_censados": pl.Int64,
        }
        return pl.DataFrame(rows, schema=schema)

    def test_ok_for_346_communes(self):
        rows = [
            {
                "codigo_comuna": f"{i:05d}",
                "viviendas_censadas": 60,
                "viviendas_particulares_ocupadas": 40,
                "viviendas_particulares_desocupadas": 15,
                "viviendas_colectivas": 5,
                "hogares_censados": 40,
            }
            for i in range(1, 347)
        ]
        df = self._make_df(rows)
        result = validate_censo_hogares_viviendas(df, None)
        self.assertEqual(result["status"], "ok")

    def test_inconsistent_housing_totals_error(self):
        rows = [
            {
                "codigo_comuna": f"{i:05d}",
                "viviendas_censadas": 100,
                "viviendas_particulares_ocupadas": 10,
                "viviendas_particulares_desocupadas": 10,
                "viviendas_colectivas": 10,  # suma 30 ≠ 100
                "hogares_censados": 10,
            }
            for i in range(1, 347)
        ]
        df = self._make_df(rows)
        result = validate_censo_hogares_viviendas(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("inconsistent" in e for e in result["errors"]))


# ── validate_indicadores ──────────────────────────────────────────────────────


class ValidateIndicadoresTests(unittest.TestCase):
    def test_ok_with_all_expected_codes(self):
        df = pl.DataFrame(
            {
                "codigo_indicador": ["uf", "dolar", "euro", "utm", "ipc"],
                "fecha": ["2024-01-01"] * 5,
                "valor": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )
        result = validate_indicadores(df, None)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["indicator_codes"], ["dolar", "euro", "ipc", "uf", "utm"])

    def test_missing_indicator_codes_error(self):
        df = pl.DataFrame(
            {
                "codigo_indicador": ["uf", "dolar"],
                "fecha": ["2024-01-01"] * 2,
                "valor": [1.0, 2.0],
            }
        )
        result = validate_indicadores(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("missing" in e for e in result["errors"]))

    def test_empty_dataset_error(self):
        df = pl.DataFrame(
            {"codigo_indicador": [], "fecha": [], "valor": []},
            schema={
                "codigo_indicador": pl.String,
                "fecha": pl.String,
                "valor": pl.Float64,
            },
        )
        result = validate_indicadores(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("empty" in e for e in result["errors"]))

    def test_fallback_mode_adds_warning(self):
        df = pl.DataFrame(
            {
                "codigo_indicador": ["uf", "dolar", "euro", "utm", "ipc"],
                "fecha": ["2024-01-01"] * 5,
                "valor": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )
        result = validate_indicadores(df, {"source_mode": "fallback"})
        self.assertEqual(result["status"], "ok")
        self.assertTrue(any("synthetic" in w for w in result["warnings"]))


# ── validate_distritos_electorales ─────────────────────────────────────────────


class ValidateDistritosElectoralesTests(unittest.TestCase):
    def _make_df(self, rows):
        schema = {
            "codigo_comuna": pl.String,
            "distrito_electoral": pl.String,
            "circunscripcion_senatorial": pl.String,
        }
        return pl.DataFrame(rows, schema=schema)

    def test_ok_for_346_communes(self):
        rows = [
            {
                "codigo_comuna": f"{i:05d}",
                "distrito_electoral": "10",
                "circunscripcion_senatorial": "5",
            }
            for i in range(1, 347)
        ]
        df = self._make_df(rows)
        result = validate_distritos_electorales(df, None)
        self.assertEqual(result["status"], "ok")

    def test_empty_dataset_error(self):
        df = pl.DataFrame(
            {
                "codigo_comuna": [],
                "distrito_electoral": [],
                "circunscripcion_senatorial": [],
            },
            schema={
                "codigo_comuna": pl.String,
                "distrito_electoral": pl.String,
                "circunscripcion_senatorial": pl.String,
            },
        )
        result = validate_distritos_electorales(df, None)
        self.assertEqual(result["status"], "error")

    def test_invalid_codigo_comuna_length_error(self):
        rows = [
            {
                "codigo_comuna": "123",  # solo 3 caracteres
                "distrito_electoral": "10",
                "circunscripcion_senatorial": "5",
            }
            for i in range(346)
        ]
        df = self._make_df(rows)
        result = validate_distritos_electorales(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("invalid" in e for e in result["errors"]))


# ── validate_establecimientos_salud ───────────────────────────────────────────


class ValidateEstablecimientosSaludTests(unittest.TestCase):
    def test_ok_minimal(self):
        df = pl.DataFrame(
            {
                "codigo_establecimiento": ["101", "102"],
                "codigo_comuna": ["01101", "01107"],
                "nombre_establecimiento": ["Hospital A", "CESFAM B"],
            }
        )
        result = validate_establecimientos_salud(df, None)
        self.assertEqual(result["status"], "ok")

    def test_empty_dataset_error(self):
        df = pl.DataFrame(
            {
                "codigo_establecimiento": [],
                "codigo_comuna": [],
                "nombre_establecimiento": [],
            },
            schema={
                "codigo_establecimiento": pl.String,
                "codigo_comuna": pl.String,
                "nombre_establecimiento": pl.String,
            },
        )
        result = validate_establecimientos_salud(df, None)
        self.assertEqual(result["status"], "error")

    def test_duplicate_codigo_establecimiento_error(self):
        df = pl.DataFrame(
            {
                "codigo_establecimiento": ["101", "101"],
                "codigo_comuna": ["01101", "01107"],
                "nombre_establecimiento": ["Hospital A", "CESFAM B"],
            }
        )
        result = validate_establecimientos_salud(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("unique" in e for e in result["errors"]))

    def test_invalid_comuna_code_length_error(self):
        df = pl.DataFrame(
            {
                "codigo_establecimiento": ["101"],
                "codigo_comuna": ["123456"],  # demasiado largo
                "nombre_establecimiento": ["Hospital A"],
            }
        )
        result = validate_establecimientos_salud(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("codigo_comuna" in e for e in result["errors"]))

    def test_unknown_comuna_codes_when_valid_list_provided(self):
        df = pl.DataFrame(
            {
                "codigo_establecimiento": ["101"],
                "codigo_comuna": ["99999"],
                "nombre_establecimiento": ["Hospital X"],
            }
        )
        result = validate_establecimientos_salud(df, None, valid_commune_codes=["01101"])
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("unknown" in e for e in result["errors"]))


# ── validate_establecimientos_educacionales ───────────────────────────────────


class ValidateEstablecimientosEducacionalesTests(unittest.TestCase):
    def test_ok_minimal(self):
        df = pl.DataFrame(
            {
                "rbd": ["1", "2"],
                "codigo_comuna": ["01101", "01107"],
                "nombre_establecimiento": ["Liceo A", "Escuela B"],
            }
        )
        result = validate_establecimientos_educacionales(df, None)
        self.assertEqual(result["status"], "ok")

    def test_empty_dataset_error(self):
        df = pl.DataFrame(
            {"rbd": [], "codigo_comuna": [], "nombre_establecimiento": []},
            schema={
                "rbd": pl.String,
                "codigo_comuna": pl.String,
                "nombre_establecimiento": pl.String,
            },
        )
        result = validate_establecimientos_educacionales(df, None)
        self.assertEqual(result["status"], "error")

    def test_duplicate_rbd_error(self):
        df = pl.DataFrame(
            {
                "rbd": ["1", "1"],
                "codigo_comuna": ["01101", "01107"],
                "nombre_establecimiento": ["Liceo A", "Escuela B"],
            }
        )
        result = validate_establecimientos_educacionales(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("unique" in e for e in result["errors"]))


class ValidateEmpresasTests(unittest.TestCase):
    """Tests para el validador del dataset de empresas (Registro de Empresas y Sociedades)."""

    def test_accepts_valid_data(self):
        """DataFrame con columnas requeridas y RUTs con DV correcto pasa la validación."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-K", "76086428-5", "12345678-5"],
                "razon_social": ["Empresa Uno SpA", "Empresa Dos EIRL", "Empresa Tres SRL"],
                "codigo_sociedad": ["SPA", "EIRL", "SRL"],
                "tipo_actuacion": ["CONSTITUCION", "CONSTITUCION", "CONSTITUCION"],
                "capital": [7000000, 25000000, 5000000],
                "fecha_registro": [None, None, None],
                "anio": [2022, 2023, 2024],
                "mes": ["Mayo", "Junio", "Julio"],
                "comuna_tributaria": ["Providencia", "Las Condes", "Valparaiso"],
                "region_tributaria": ["13", "13", "05"],
                "comuna_social": ["Providencia", "Las Condes", "Valparaiso"],
                "region_social": ["13", "13", "05"],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["record_count"], 3)
        # Debe tener al menos el warning de cobertura limitada al régimen simplificado
        self.assertGreater(len(result["warnings"]), 0)

    def test_rejects_empty(self):
        """DataFrame vacío es rechazado."""
        df = pl.DataFrame()
        result = validate_empresas(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("empty" in e for e in result["errors"]))

    def test_rejects_negative_capital(self):
        """Capital negativo es rechazado."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-K"],
                "razon_social": ["Test SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [2022],
                "comuna_tributaria": ["Santiago"],
                "region_tributaria": ["13"],
                "capital": [-1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("negative capital" in e for e in result["errors"]))

    def test_rejects_anio_before_2013(self):
        """Año anterior a 2013 (inicio del RES) es rechazado."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-K"],
                "razon_social": ["Antigua SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [2010],
                "comuna_tributaria": ["Santiago"],
                "region_tributaria": ["13"],
                "capital": [1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("anio < 2013" in e for e in result["errors"]))

    def test_warns_unknown_sociedad(self):
        """Código de sociedad desconocido genera warning."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-K"],
                "razon_social": ["Misteriosa Ltda"],
                "codigo_sociedad": ["XYZ"],
                "fecha_registro": [None],
                "anio": [2024],
                "comuna_tributaria": ["Santiago"],
                "region_tributaria": ["13"],
                "capital": [1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "ok")
        self.assertTrue(any("XYZ" in str(w) for w in result["warnings"]))

    def test_warns_invalid_rut_format(self):
        """RUT con formato inválido (sin guion, caracteres no numéricos) genera warning."""
        df = pl.DataFrame(
            {
                "rut": ["abc", "1234", "12.345.678-5"],
                "razon_social": ["A", "B", "C"],
                "codigo_sociedad": ["SPA", "SPA", "SPA"],
                "fecha_registro": [None, None, None],
                "anio": [2024, 2024, 2024],
                "comuna_tributaria": ["Santiago", "Santiago", "Santiago"],
                "region_tributaria": ["13", "13", "13"],
                "capital": [1000, 1000, 1000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "ok")
        self.assertTrue(any("invalid format" in w for w in result["warnings"]))

    def test_warns_invalid_rut_dv(self):
        """RUT con formato correcto pero dígito verificador incorrecto genera warning."""
        df = pl.DataFrame(
            {
                "rut": ["76086428-0"],  # DV incorrecto: base 76086428 → DV real es 5
                "razon_social": ["Test SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [2024],
                "comuna_tributaria": ["Santiago"],
                "region_tributaria": ["13"],
                "capital": [1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "ok")  # DV malo es warning, no error
        self.assertTrue(any("invalid check digit" in w for w in result["warnings"]))

    def test_rut_with_dots_accepted(self):
        """RUT con puntos (formato chileno estándar) es aceptado."""
        df = pl.DataFrame(
            {
                "rut": ["76.086.428-5"],  # con puntos → debe limpiarse y validar
                "razon_social": ["Empresa Puntos SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [2024],
                "comuna_tributaria": ["Las Condes"],
                "region_tributaria": ["13"],
                "capital": [5000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "ok")
        # No debe haber warning de formato (los puntos se limpian)
        self.assertFalse(any("invalid format" in w for w in result["warnings"]))

    def test_rut_with_lowercase_k_accepted(self):
        """RUT con dígito verificador 'k' minúscula es aceptado."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-k"],  # 'k' minúscula es válida
                "razon_social": ["Empresa K SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [2024],
                "comuna_tributaria": ["Providencia"],
                "region_tributaria": ["13"],
                "capital": [3000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "ok")
        # No debe haber warning de formato ni de DV incorrecto
        self.assertFalse(any("invalid format" in w for w in result["warnings"]))
        self.assertFalse(any("invalid check digit" in w for w in result["warnings"]))

    def test_null_rut_error(self):
        """RUT nulo genera error."""
        df = pl.DataFrame(
            {
                "rut": [None],
                "razon_social": ["Sin RUT SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [2024],
                "comuna_tributaria": ["Santiago"],
                "region_tributaria": ["13"],
                "capital": [1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertTrue(any("null RUT" in e for e in result["errors"]))

    def test_rejects_missing_columns(self):
        """DataFrame sin columnas requeridas genera error."""
        df = pl.DataFrame({"rut": ["76286049-K"]})
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("missing columns" in e for e in result["errors"]))

    def test_warns_duplicate_rut_rows(self):
        """Filas duplicadas en (rut, razon_social, fecha_registro) generan warning."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-K", "76286049-K"],
                "razon_social": ["Duplicada SpA", "Duplicada SpA"],
                "codigo_sociedad": ["SPA", "SPA"],
                "fecha_registro": [None, None],
                "anio": [2024, 2024],
                "comuna_tributaria": ["Santiago", "Santiago"],
                "region_tributaria": ["13", "13"],
                "capital": [1000000, 1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertTrue(any("duplicate" in w for w in result["warnings"]))

    def test_rejects_invalid_region_tributaria(self):
        """region_tributaria con largo != 2 genera error."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-K"],
                "razon_social": ["Test SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [2024],
                "comuna_tributaria": ["Santiago"],
                "region_tributaria": ["135"],
                "capital": [1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("region_tributaria" in e for e in result["errors"]))

    def test_rejects_null_anio(self):
        """anio nulo genera error."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-K"],
                "razon_social": ["Test SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [None],
                "comuna_tributaria": ["Santiago"],
                "region_tributaria": ["13"],
                "capital": [1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "live"})
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("anio < 2013" in e for e in result["errors"]))

    def test_warns_fallback_mode(self):
        """source_mode fallback genera warning."""
        df = pl.DataFrame(
            {
                "rut": ["76286049-K"],
                "razon_social": ["Fallback SpA"],
                "codigo_sociedad": ["SPA"],
                "fecha_registro": [None],
                "anio": [2024],
                "comuna_tributaria": ["Santiago"],
                "region_tributaria": ["13"],
                "capital": [1000000],
            }
        )
        result = validate_empresas(df, {"source_mode": "fallback"})
        self.assertEqual(result["status"], "ok")
        self.assertTrue(any("fallback" in w for w in result["warnings"]))


# ── Property-based tests (hypothesis) ──────────────────────────────────────────


class CUTInvariantProperties(unittest.TestCase):
    """Las invariantes de códigos CUT deben cumplirse para cualquier entrada válida."""

    def test_codigo_comuna_siempre_cinco_caracteres(self):
        """Si validate_comunas retorna 'ok', todos los códigos comuna miden 5."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        @given(
            n=st.integers(min_value=1, max_value=50),
            seed=st.integers(min_value=1, max_value=99999),
        )
        @settings(max_examples=100)
        def _property(n, seed):
            codes = [f"{i:05d}" for i in range(1, n + 1)]
            df = pl.DataFrame(
                {
                    "codigo_region": ["01"] * n,
                    "codigo_provincia": ["011"] * n,
                    "codigo_comuna": codes,
                    "nombre_region": ["Tarapacá"] * n,
                    "nombre_provincia": ["Iquique"] * n,
                    "nombre_comuna": [f"Comuna {c}" for c in codes],
                    "nombre_comuna_clean": [f"comuna {c}" for c in codes],
                    "abreviatura": ["TAR"] * n,
                    "latitud_cabecera": [-20.0] * n,
                    "longitud_cabecera": [-70.0] * n,
                    "poblacion_estimada": [1000] * n,
                }
            )
            result = validate_comunas(df, {"source_mode": "live"})
            if result["status"] == "ok":
                for code in df["codigo_comuna"].to_list():
                    assert len(code) == 5, f"CUT inválido: {code}"
                for code in df["codigo_provincia"].to_list():
                    assert len(code) == 3, f"CUT provincia inválido: {code}"
                for code in df["codigo_region"].to_list():
                    assert len(code) == 2, f"CUT región inválido: {code}"

        _property()

    def test_nombre_comuna_clean_sin_caracteres_especiales(self):
        """nombre_comuna_clean nunca debe tener tildes ni ñ."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        # Caracteres que la función validate_comunas debe rechazar en clean
        FORBIDDEN = set("áéíóúüñ")

        @given(
            n=st.integers(min_value=1, max_value=30),
        )
        @settings(max_examples=100)
        def _property(n):
            codes = [f"{i:05d}" for i in range(1, n + 1)]
            df = pl.DataFrame(
                {
                    "codigo_region": ["01"] * n,
                    "codigo_provincia": ["011"] * n,
                    "codigo_comuna": codes,
                    "nombre_region": ["Tarapacá"] * n,
                    "nombre_provincia": ["Iquique"] * n,
                    "nombre_comuna": [f"Comuna {c}" for c in codes],
                    "nombre_comuna_clean": [f"comuna {c}" for c in codes],
                    "abreviatura": ["TAR"] * n,
                    "latitud_cabecera": [-20.0] * n,
                    "longitud_cabecera": [-70.0] * n,
                    "poblacion_estimada": [1000] * n,
                }
            )
            result = validate_comunas(df, {"source_mode": "live"})
            if result["status"] == "ok":
                for name in df["nombre_comuna_clean"].to_list():
                    assert not any(c in name for c in FORBIDDEN), (
                        f"nombre_comuna_clean contiene caracteres prohibidos: {name}"
                    )
                    assert name == name.lower(), f"nombre_comuna_clean no es lowercase: {name}"

        _property()


class ValidatorContractProperties(unittest.TestCase):
    """Todo validador debe cumplir el contrato de retorno, sin importar la entrada."""

    def test_todo_validador_retorna_dict_con_status_errors_warnings(self):
        """Cualquier DataFrame pasado a un validador produce {status, errors, warnings}."""
        from hypothesis import given, settings
        from hypothesis import strategies as st

        # Validadores que aceptan solo 1 arg (df)
        VALIDATORS_1_ARG = [validate_regiones, validate_provincias]
        # Validadores que aceptan 2 args (df, metadata)
        VALIDATORS_2_ARGS = [
            validate_comunas,
            validate_indicadores,
            validate_censo_comunal,
            validate_censo_hogares_viviendas,
            validate_distritos_electorales,
            validate_establecimientos_salud,
            validate_establecimientos_educacionales,
        ]

        @given(
            n_cols=st.integers(min_value=0, max_value=10),
            n_rows=st.integers(min_value=0, max_value=5),
        )
        @settings(max_examples=50)
        def _property(n_cols, n_rows):
            # Construir un DataFrame arbitrario con columnas genéricas
            cols = {f"col_{i}": [f"v{j}" for j in range(n_rows)] for i in range(n_cols)}
            cols["codigo_comuna"] = [f"{j:05d}" for j in range(n_rows)]
            df = pl.DataFrame(cols)

            for validator in VALIDATORS_1_ARG:
                _check_validator(validator, df)

            for validator in VALIDATORS_2_ARGS:
                _check_validator(validator, df, metadata={"source_mode": "live"})

        def _check_validator(validator, df, *, metadata=None):
            try:
                args = (df,) if metadata is None else (df, metadata)
                result = validator(*args)
            except Exception:
                # Crash ante entradas arbitrarias es aceptable (ej. falta
                # de columna requerida). Hypothesis encuentra estos casos
                # para que se documenten, no para que fallen el build.
                return
            _assert_validator_contract(validator.__name__, result)

        def _assert_validator_contract(name, result):
            assert isinstance(result, dict), f"{name} no retornó dict: {type(result)}"
            assert "status" in result, f"{name} no tiene 'status'"
            assert result["status"] in ("ok", "warn", "error"), (
                f"{name} status inválido: {result['status']}"
            )
            assert isinstance(result["errors"], list), f"{name} errors no es list"

        _property()


# ── contracts.py tests ──────────────────────────────────────────────────────


class ContractTypeTests(unittest.TestCase):
    """Tests para contract_type() del módulo contracts."""

    def _contract_type(self, dtype):
        from src.chile_hub.contracts import contract_type

        return contract_type(dtype)

    def test_string_types(self):
        self.assertEqual(self._contract_type("String"), "string")

    def test_integer_types(self):
        for t in ("Int8", "Int16", "Int32", "Int64", "UInt8", "UInt16", "UInt32", "UInt64"):
            self.assertEqual(self._contract_type(t), "integer")

    def test_float_types(self):
        self.assertEqual(self._contract_type("Float32"), "float")
        self.assertEqual(self._contract_type("Float64"), "float")

    def test_date_type(self):
        self.assertEqual(self._contract_type("Date"), "date")

    def test_boolean_type(self):
        self.assertEqual(self._contract_type("Boolean"), "boolean")

    def test_unknown_type_defaults_to_lower(self):
        self.assertEqual(self._contract_type("Time"), "time")
        self.assertEqual(self._contract_type("List"), "list")


_COMMUNES_CONTRACT = {
    "dataset": "comunas",
    "primary_key": ["codigo_comuna"],
    "required_columns": ["codigo_comuna", "nombre_comuna", "nombre_comuna_clean"],
    "column_types": {
        "codigo_comuna": "string",
        "nombre_comuna": "string",
        "codigo_region": "string",
    },
    "fixed_width_columns": {"codigo_comuna": 5, "codigo_region": 2},
    "expected_record_count": 3,
    "coverage_policy": "full",
    "publish_outputs": [],
}


class VerifyDatasetContractTests(unittest.TestCase):
    """Tests para verify_dataset_contract() del módulo contracts."""

    def _verify(self, contract=None, df=None, **kwargs):
        from src.chile_hub.contracts import verify_dataset_contract

        if contract is None:
            contract = _COMMUNES_CONTRACT
        if df is None:
            df = pl.DataFrame(
                {
                    "codigo_comuna": ["01101", "01107", "01105"],
                    "nombre_comuna": ["Iquique", "Alto Hospicio", "Pica"],
                    "nombre_comuna_clean": ["iquique", "alto hospicio", "pica"],
                    "codigo_region": ["01", "01", "01"],
                }
            )
        return verify_dataset_contract("comunas", contract, df, **kwargs)

    def test_ok_minimal(self):
        result = self._verify()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["dataset"], "comunas")

    def test_dataset_name_mismatch(self):
        from src.chile_hub.contracts import verify_dataset_contract

        result = verify_dataset_contract("otro", _COMMUNES_CONTRACT, pl.DataFrame())
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("contrato" in e for e in result["errors"]))

    def test_missing_required_columns(self):
        df = pl.DataFrame({"codigo_comuna": ["01101"]})
        result = self._verify(df=df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("Faltan columnas" in e for e in result["errors"]))

    def test_wrong_column_type(self):
        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101"],
                "nombre_comuna": ["Iquique"],
                "nombre_comuna_clean": ["iquique"],
                "codigo_region": [1],  # debe ser string
            }
        )
        result = self._verify(df=df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("tipo" in e.lower() for e in result["errors"]))

    def test_duplicate_primary_key(self):
        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101", "01101"],
                "nombre_comuna": ["Iquique", "Iquique"],
                "nombre_comuna_clean": ["iquique", "iquique"],
                "codigo_region": ["01", "01"],
            }
        )
        result = self._verify(df=df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("duplicado" in e for e in result["errors"]))

    def test_null_in_primary_key(self):
        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101", None],
                "nombre_comuna": ["Iquique", "Alto Hospicio"],
                "nombre_comuna_clean": ["iquique", "alto hospicio"],
                "codigo_region": ["01", "01"],
            }
        )
        result = self._verify(df=df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("nulos" in e for e in result["errors"]))

    def test_fixed_width_violation(self):
        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101", "1101"],  # "1101" tiene largo 4
                "nombre_comuna": ["Iquique", "Valparaíso"],
                "nombre_comuna_clean": ["iquique", "valparaiso"],
                "codigo_region": ["01", "01"],
            }
        )
        result = self._verify(df=df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("ancho" in e for e in result["errors"]))

    def test_record_count_warning_non_strict(self):
        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101", "01107"],
                "nombre_comuna": ["Iquique", "Alto Hospicio"],
                "nombre_comuna_clean": ["iquique", "alto hospicio"],
                "codigo_region": ["01", "01"],
            }
        )
        result = self._verify(df=df)  # 2 filas, contrato espera 3
        self.assertEqual(result["status"], "ok")  # warning no bloquea
        self.assertGreater(len(result["warnings"]), 0)

    def test_record_count_error_strict(self):
        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101", "01107"],
                "nombre_comuna": ["Iquique", "Alto Hospicio"],
                "nombre_comuna_clean": ["iquique", "alto hospicio"],
                "codigo_region": ["01", "01"],
            }
        )
        result = self._verify(df=df, strict=True)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("Registros" in e for e in result["errors"]))

    def test_missing_publish_output(self):
        from src.chile_hub.contracts import verify_dataset_contract

        contract = dict(_COMMUNES_CONTRACT)
        contract["publish_outputs"] = ["parquet", "json"]
        df = pl.DataFrame(
            {
                "codigo_comuna": ["01101"],
                "nombre_comuna": ["Iquique"],
                "nombre_comuna_clean": ["iquique"],
                "codigo_region": ["01"],
            }
        )
        result = verify_dataset_contract(
            "comunas",
            contract,
            df,
            outputs={"parquet": "data/normalized/comunas.parquet"},
        )
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("output" in e for e in result["errors"]))


class PobrezaComunalValidatorTests(unittest.TestCase):
    """Tests unitarios para validate_pobreza_comunal."""

    def setUp(self):
        self.valid_codes = [f"{i:05d}" for i in range(1, 347)]

    def _make_df(self, rows):
        return pl.DataFrame(
            rows,
            schema={
                "codigo_region": pl.String,
                "codigo_comuna": pl.String,
                "nombre_comuna": pl.String,
                "anio": pl.Int64,
                "dimension": pl.String,
                "tasa": pl.Float64,
                "limite_inferior": pl.Float64,
                "limite_superior": pl.Float64,
                "metodologia": pl.String,
                "fuente": pl.String,
                "url_fuente": pl.String,
                "fecha_fuente": pl.String,
            },
        )

    def test_valid_data_returns_ok(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "13",
                    "codigo_comuna": "13101",
                    "nombre_comuna": "Santiago",
                    "anio": 2022,
                    "dimension": "ingresos",
                    "tasa": 4.5,
                    "limite_inferior": 3.2,
                    "limite_superior": 6.1,
                    "metodologia": "SAE",
                    "fuente": "MDS",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                }
            ]
        )
        result = validate_pobreza_comunal(df, valid_commune_codes=self.valid_codes)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["errors"], [])

    def test_empty_dataframe_returns_error(self):
        df = self._make_df([])
        result = validate_pobreza_comunal(df)
        self.assertEqual(result["status"], "error")

    def test_missing_columns_returns_error(self):
        df = pl.DataFrame({"columna_random": [1]})
        result = validate_pobreza_comunal(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("missing" in e for e in result["errors"]))

    def test_tasa_out_of_bounds(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "13",
                    "codigo_comuna": "13101",
                    "nombre_comuna": "Santiago",
                    "anio": 2022,
                    "dimension": "ingresos",
                    "tasa": 150.0,
                    "limite_inferior": 140.0,
                    "limite_superior": 160.0,
                    "metodologia": "SAE",
                    "fuente": "MDS",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                }
            ]
        )
        result = validate_pobreza_comunal(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("0-100" in e for e in result["errors"]))

    def test_invalid_cut_format(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "13",
                    "codigo_comuna": "1101",
                    "nombre_comuna": "Iquique",
                    "anio": 2022,
                    "dimension": "ingresos",
                    "tasa": 4.5,
                    "limite_inferior": 3.2,
                    "limite_superior": 6.1,
                    "metodologia": "SAE",
                    "fuente": "MDS",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                }
            ]
        )
        result = validate_pobreza_comunal(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("invalid length" in e for e in result["errors"]))

    def test_unknown_communes_emit_warning_not_error(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "99",
                    "codigo_comuna": "99999",
                    "nombre_comuna": "Ficticia",
                    "anio": 2022,
                    "dimension": "ingresos",
                    "tasa": 4.5,
                    "limite_inferior": 3.2,
                    "limite_superior": 6.1,
                    "metodologia": "SAE",
                    "fuente": "MDS",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                }
            ]
        )
        result = validate_pobreza_comunal(df, valid_commune_codes=["13101"])
        self.assertEqual(result["status"], "ok")
        self.assertTrue(
            any("not in DPA" in w or "unknown" in w.lower() for w in result["warnings"])
        )

    def test_fallback_mode_warns(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "13",
                    "codigo_comuna": "13101",
                    "nombre_comuna": "Santiago",
                    "anio": 2022,
                    "dimension": "ingresos",
                    "tasa": 4.5,
                    "limite_inferior": 3.2,
                    "limite_superior": 6.1,
                    "metodologia": "SAE",
                    "fuente": "MDS",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                }
            ]
        )
        result = validate_pobreza_comunal(df, metadata={"source_mode": "fallback"})
        self.assertEqual(result["status"], "ok")
        self.assertTrue(any("fallback" in w for w in result["warnings"]))


class ConsumoElectricoValidatorTests(unittest.TestCase):
    """Tests unitarios para validate_consumo_electrico_comunal."""

    def setUp(self):
        self.valid_codes = [f"{i:05d}" for i in range(1, 347)]

    def _make_df(self, rows):
        return pl.DataFrame(
            rows,
            schema={
                "codigo_region": pl.String,
                "codigo_comuna": pl.String,
                "nombre_comuna": pl.String,
                "anio": pl.Int64,
                "tipo_cliente": pl.String,
                "consumo_kwh": pl.Float64,
                "numero_clientes": pl.Int64,
                "fuente": pl.String,
                "url_fuente": pl.String,
                "fecha_fuente": pl.String,
            },
        )

    def test_valid_data_returns_ok(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "13",
                    "codigo_comuna": "13101",
                    "nombre_comuna": "Santiago",
                    "anio": 2023,
                    "tipo_cliente": "Residencial",
                    "consumo_kwh": 1250000000.0,
                    "numero_clientes": 150000,
                    "fuente": "CNE",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                }
            ]
        )
        result = validate_consumo_electrico_comunal(df, valid_commune_codes=self.valid_codes)
        self.assertEqual(result["status"], "ok")

    def test_empty_dataframe_returns_error(self):
        df = self._make_df([])
        result = validate_consumo_electrico_comunal(df)
        self.assertEqual(result["status"], "error")

    def test_negative_consumo_returns_error(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "13",
                    "codigo_comuna": "13101",
                    "nombre_comuna": "Santiago",
                    "anio": 2023,
                    "tipo_cliente": "Residencial",
                    "consumo_kwh": -100.0,
                    "numero_clientes": 150,
                    "fuente": "CNE",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                }
            ]
        )
        result = validate_consumo_electrico_comunal(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("negative" in e for e in result["errors"]))

    def test_invalid_cut_format(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "13",
                    "codigo_comuna": "1101",
                    "nombre_comuna": "Iquique",
                    "anio": 2023,
                    "tipo_cliente": "Residencial",
                    "consumo_kwh": 1000.0,
                    "numero_clientes": 100,
                    "fuente": "CNE",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                }
            ]
        )
        result = validate_consumo_electrico_comunal(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("invalid length" in e for e in result["errors"]))

    def test_duplicate_key_returns_error(self):
        df = self._make_df(
            [
                {
                    "codigo_region": "13",
                    "codigo_comuna": "13101",
                    "nombre_comuna": "Santiago",
                    "anio": 2023,
                    "tipo_cliente": "Residencial",
                    "consumo_kwh": 1000.0,
                    "numero_clientes": 100,
                    "fuente": "CNE",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                },
                {
                    "codigo_region": "13",
                    "codigo_comuna": "13101",
                    "nombre_comuna": "Santiago",
                    "anio": 2023,
                    "tipo_cliente": "Residencial",
                    "consumo_kwh": 2000.0,
                    "numero_clientes": 100,
                    "fuente": "CNE",
                    "url_fuente": "https://example.com",
                    "fecha_fuente": "2026-06-30",
                },
            ]
        )
        result = validate_consumo_electrico_comunal(df)
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("duplicate" in e for e in result["errors"]))


class PartidosPoliticosValidatorTests(unittest.TestCase):
    """Tests unitarios para validate_partidos_politicos (Plan 023)."""

    def _make_df(self, rows):
        return pl.DataFrame(
            rows,
            schema={
                "id_partido": pl.String,
                "nombre": pl.String,
                "sigla": pl.String,
                "estado_legal": pl.String,
                "fecha_constitucion": pl.String,
                "ambito": pl.String,
                "fuente": pl.String,
                "url_fuente": pl.String,
                "fecha_consulta": pl.String,
            },
        )

    def test_valid_data_returns_ok(self):
        df = self._make_df(
            [
                {
                    "id_partido": "1",
                    "nombre": "Unión Demócrata Independiente",
                    "sigla": "UDI",
                    "estado_legal": "constituido",
                    "fecha_constitucion": "1989-05-03",
                    "ambito": None,
                    "fuente": "Cámara",
                    "url_fuente": "https://example.com",
                    "fecha_consulta": "2026-07-06",
                }
            ]
        )
        result = validate_partidos_politicos(df)
        self.assertEqual(result["status"], "ok")

    def test_nulls_en_estado_legal_no_fallan(self):
        """Un partido sin match en SERVEL queda con estado_legal nulo — no es error."""
        df = self._make_df(
            [
                {
                    "id_partido": "2",
                    "nombre": "Partido Histórico",
                    "sigla": "PH",
                    "estado_legal": None,
                    "fecha_constitucion": None,
                    "ambito": None,
                    "fuente": "Cámara",
                    "url_fuente": "https://example.com",
                    "fecha_consulta": "2026-07-06",
                }
            ]
        )
        result = validate_partidos_politicos(df)
        self.assertEqual(result["status"], "ok")

    def test_empty_dataframe_returns_error(self):
        result = validate_partidos_politicos(self._make_df([]))
        self.assertEqual(result["status"], "error")

    def test_duplicate_key_returns_error(self):
        row = {
            "id_partido": "1",
            "nombre": "Partido X",
            "sigla": "PX",
            "estado_legal": None,
            "fecha_constitucion": None,
            "ambito": None,
            "fuente": "Cámara",
            "url_fuente": "https://example.com",
            "fecha_consulta": "2026-07-06",
        }
        result = validate_partidos_politicos(self._make_df([row, row]))
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("duplicate" in e for e in result["errors"]))

    def test_estado_legal_fuera_de_dominio_es_error(self):
        df = self._make_df(
            [
                {
                    "id_partido": "1",
                    "nombre": "Partido X",
                    "sigla": "PX",
                    "estado_legal": "activo",
                    "fecha_constitucion": None,
                    "ambito": None,
                    "fuente": "Cámara",
                    "url_fuente": "https://example.com",
                    "fecha_consulta": "2026-07-06",
                }
            ]
        )
        result = validate_partidos_politicos(df)
        self.assertEqual(result["status"], "error")


class AutoridadesElectasValidatorTests(unittest.TestCase):
    """Tests unitarios para validate_autoridades_electas (Plan 023)."""

    def _make_df(self, rows):
        return pl.DataFrame(
            rows,
            schema={
                "id_autoridad": pl.String,
                "nombre": pl.String,
                "cargo": pl.String,
                "institucion": pl.String,
                "partido": pl.String,
                "codigo_comuna": pl.String,
                "codigo_region": pl.String,
                "fuente": pl.String,
                "url_fuente": pl.String,
                "fecha_consulta": pl.String,
            },
        )

    def _row(self, **overrides):
        row = {
            "id_autoridad": "senador_1",
            "nombre": "Nombre Apellido",
            "cargo": "senador",
            "institucion": "Senado",
            "partido": "Partido X",
            "codigo_comuna": None,
            "codigo_region": "02",
            "fuente": "Senado",
            "url_fuente": "https://example.com",
            "fecha_consulta": "2026-07-06",
        }
        row.update(overrides)
        return row

    def test_valid_data_returns_ok(self):
        result = validate_autoridades_electas(self._make_df([self._row()]))
        self.assertEqual(result["status"], "ok")

    def test_empty_dataframe_returns_error(self):
        result = validate_autoridades_electas(self._make_df([]))
        self.assertEqual(result["status"], "error")

    def test_duplicate_key_returns_error(self):
        row = self._row()
        result = validate_autoridades_electas(self._make_df([row, row]))
        self.assertEqual(result["status"], "error")
        self.assertTrue(any("duplicate" in e for e in result["errors"]))

    def test_cargo_fuera_de_dominio_v1_es_error(self):
        df = self._make_df([self._row(id_autoridad="alcalde_1", cargo="alcalde")])
        result = validate_autoridades_electas(df)
        self.assertEqual(result["status"], "error")

    def test_codigo_region_invalido_es_error(self):
        df = self._make_df([self._row(codigo_region="2")])
        result = validate_autoridades_electas(df)
        self.assertEqual(result["status"], "error")

    def test_codigo_region_nulo_no_falla(self):
        """Diputados no tienen codigo_region en v1 — nulo no debe fallar la validación."""
        df = self._make_df(
            [self._row(id_autoridad="diputado_1", cargo="diputado", codigo_region=None)]
        )
        result = validate_autoridades_electas(df)
        self.assertEqual(result["status"], "ok")


# ── validate_puntos_interes ─────────────────────────────────────────────────────


class ValidatePuntosInteresTests(unittest.TestCase):
    """Tests para validate_puntos_interes (OpenStreetMap POIs)."""

    @staticmethod
    def _valid_row(**overrides):
        row = {
            "osm_id": 1,
            "nombre": "Plaza de Armas",
            "categoria": "amenidad",
            "tipo": "plaza",
            "latitud": -33.45,
            "longitud": -70.67,
            "codigo_comuna": "13101",
        }
        row.update(overrides)
        return row

    @staticmethod
    def _make_df(rows):
        return pl.DataFrame(
            rows,
            schema={
                "osm_id": pl.Int64,
                "nombre": pl.String,
                "categoria": pl.String,
                "tipo": pl.String,
                "latitud": pl.Float64,
                "longitud": pl.Float64,
                "codigo_comuna": pl.String,
            },
        )

    def test_ok_minimal(self):
        df = self._make_df([self._valid_row()])
        result = validate_puntos_interes(df, metadata={"source_mode": "live"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["record_count"], 1)

    def test_missing_columns_returns_error(self):
        df = pl.DataFrame(
            {"osm_id": []},
            schema={"osm_id": pl.Int64},
        )
        result = validate_puntos_interes(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(
            any("missing columns" in e for e in result["errors"]),
            msg=f"Expected 'missing columns' error, got: {result['errors']}",
        )

    def test_out_of_bounds_coordinates_returns_error(self):
        df = self._make_df([self._valid_row(latitud=-60.0)])
        result = validate_puntos_interes(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(
            any("outside Chile" in e for e in result["errors"]),
            msg=f"Expected bounds error, got: {result['errors']}",
        )

    def test_invalid_codigo_comuna_returns_error(self):
        df = self._make_df([self._valid_row(codigo_comuna="123")])
        result = validate_puntos_interes(df, None)
        self.assertEqual(result["status"], "error")
        self.assertTrue(
            any("5-char" in e for e in result["errors"]),
            msg=f"Expected '5-char' error, got: {result['errors']}",
        )


if __name__ == "__main__":
    unittest.main()
