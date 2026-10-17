"""Pruebas sin red del candidato de precipitaciones DGAC."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import research_dgac_precipitaciones as dgac


def sample_csv(year=2025, month=7, *, invalid=None, missing=False):
    """Cuatro estaciones x 28 días: muestra sintética con layout observado en CKAN."""
    output = io.StringIO()
    writer = csv.writer(output)
    for station in range(4):
        for day in range(1, 29):
            rain = "S/I" if missing and day == 2 and station == 0 else "0.0"
            if invalid is not None and day == 1 and station == 0:
                rain = invalid
            writer.writerow(
                [
                    180005 + station,
                    "Chacalluta, Arica Ap.",
                    "18° 21' 20'' S",
                    51,
                    year,
                    month,
                    day,
                    rain,
                ]
            )
    return output.getvalue().encode("utf-8")


class DgacResearchTests(unittest.TestCase):
    def test_headerless_csv_preserves_first_observation_and_station_id(self):
        # CKAN datastore_search interpreta la primera observación como cabecera.
        rows = dgac.parse_csv(
            sample_csv(),
            year=2025,
            month=7,
            url="https://datos.gob.cl/x",
            license_id="cc-zero",
        )
        self.assertEqual(len(rows), 112)
        self.assertEqual(rows[0]["fecha"], "2025-07-01")
        self.assertEqual(rows[0]["id_estacion"], "180005")
        self.assertEqual(rows[0]["precipitacion_mm"], "0.0")

    def test_legacy_source_formats_in_existing_header_regression(self):
        # La DGAC 2013 usa ';' y comas dentro del nombre de estación.
        line = "180005;Chacalluta, Arica Ap.;18&deg 21' 20'' S;50;2013;01;01;0.0"
        content = "\n".join([line.replace(";01;0.0", f";{day:02d};0.0") for day in range(1, 29)])
        # 4 estaciones x 28 días para superar el gate mínimo.
        content = "\n".join(
            content.replace("180005;", f"{180005 + station};") for station in range(4)
        ).encode("utf-8")
        rows = dgac.parse_csv(
            content,
            year=2013,
            month=1,
            url="https://datos.gob.cl/legacy.csv",
            license_id="cc-by",
        )
        self.assertEqual(len(rows), 112)
        self.assertIn("°", rows[0]["latitud_dms"])
        # En 2016 el origen sí incluye cabecera; no contaría como observación.
        header = "CodigoNacional,NombreEstacion,Latitud,Altura,Año,Mes,Dia,SumaDiaria\n"
        rows = dgac.parse_csv(
            header.encode("utf-8") + sample_csv(2016, 1),
            year=2016,
            month=1,
            url="https://datos.gob.cl/with-header.csv",
            license_id="cc-by",
        )
        self.assertEqual(len(rows), 112)
        self.assertEqual(rows[0]["fecha"], "2016-01-01")
        # 2026 usa encabezados en mayúsculas y terminología diferente.
        modern = (
            "CODIGO NACIONAL,NOMBRE DE LA ESTACIÓN,LATITUD,ALTITUD,AÑO,MES,DÍA,PRECIPITACIÓN (MM)\n"
        )
        rows = dgac.parse_csv(
            modern.encode("utf-8") + sample_csv(2026, 1),
            year=2026,
            month=1,
            url="https://datos.gob.cl/2026.csv",
            license_id="cc-zero",
        )
        self.assertEqual(len(rows), 112)
        self.assertEqual(rows[0]["fecha"], "2026-01-01")
        # Un encabezado T.Maxima/T.Minima es temperatura, no lluvia.
        with self.assertRaisesRegex(dgac.SourceError, "Primera fila desconocida"):
            dgac.parse_csv(
                (
                    "CodigoNacional,NombreEstacion,Latitud,Altura,Año,Mes,Dia,T.Maxima,T.Minima\n"
                ).encode()
                + sample_csv(2017, 1),
                year=2017,
                month=1,
                url="https://datos.gob.cl/2017.csv",
                license_id="cc-by",
            )

    def test_missing_measurement_is_not_zero(self):
        rows = dgac.parse_csv(
            sample_csv(missing=True),
            year=2025,
            month=7,
            url="https://datos.gob.cl/x",
            license_id="cc-zero",
        )
        self.assertEqual(rows[1]["precipitacion_mm"], "")

    def test_negative_precipitation_fails(self):
        with self.assertRaisesRegex(dgac.SourceError, "negativa"):
            dgac.parse_csv(
                sample_csv(invalid="-2"),
                year=2025,
                month=7,
                url="https://datos.gob.cl/x",
                license_id="cc-zero",
            )

    def test_wrong_month_fails(self):
        with self.assertRaisesRegex(dgac.SourceError, "fuera del período"):
            dgac.parse_csv(
                sample_csv(month=8),
                year=2025,
                month=7,
                url="https://datos.gob.cl/x",
                license_id="cc-zero",
            )

    def test_ambiguous_or_incomplete_resources_fail(self):
        package = {
            "resources": [
                {
                    "name": "Precipitacion_072025.csv",
                    "format": "csv",
                    "url": "https://datos.gob.cl/x/precipitacion_072025.csv",
                }
            ]
        }
        with self.assertRaisesRegex(dgac.SourceError, "Faltan CSV"):
            dgac.resources_for_package(package, 2025, range(7, 13))
        duplicated = {"resources": [*package["resources"], *package["resources"]]}
        self.assertEqual(len(dgac.resources_for_package(duplicated, 2025, range(7, 8))), 2)

    def test_full_two_year_harvest_is_atomic_and_source_traceable(self):
        def get_package(name):
            year, semester = next(k for k, v in dgac.PACKAGES.items() if v == name)
            months = range(1, 7) if semester == 1 else range(7, 13)
            return {
                "license_id": "cc-by" if (year, semester) == (2024, 1) else "cc-zero",
                "resources": [
                    {
                        "name": f"Precipitacion_{month:02d}{year}.csv",
                        "format": "csv",
                        "url": f"https://datos.gob.cl/example/precipitacion_{month:02d}{year}.csv",
                    }
                    for month in months
                ],
            }

        def request(url, *, retries=3):
            token = url.rsplit("/", 1)[-1].removesuffix(".csv").removeprefix("precipitacion_")
            month, year = int(token[:2]), int(token[2:])
            return sample_csv(year, month)

        with tempfile.TemporaryDirectory() as tmp:
            outfile = Path(tmp) / "observaciones.csv"
            with (
                patch.object(dgac, "_package", side_effect=get_package),
                patch.object(dgac, "_request", side_effect=request),
            ):
                meta = dgac.harvest(outfile, start_year=2024, end_year=2025)
            self.assertEqual(meta["months"], 24)
            self.assertEqual(meta["record_count"], 112 * 24)
            self.assertEqual(meta["station_count"], 4)
            self.assertEqual(len(meta["source_files"]), 24)
            self.assertTrue(outfile.is_file())
            self.assertTrue(outfile.with_suffix(".metadata.json").is_file())
            self.assertEqual(hashlib.sha256(outfile.read_bytes()).hexdigest(), meta["sha256"])
            with outfile.open(encoding="utf-8", newline="") as inp:
                rows = list(csv.DictReader(inp))
            self.assertEqual(len(rows), 112 * 24)
            self.assertEqual(rows[0]["fecha"], "2024-01-01")
            self.assertEqual(rows[-1]["fecha"], "2025-12-28")
            self.assertEqual(rows[0]["licencia_fuente"], "cc-by")
            self.assertEqual(rows[-1]["licencia_fuente"], "cc-zero")
            self.assertEqual(
                json.loads(outfile.with_suffix(".metadata.json").read_text())["record_count"],
                len(rows),
            )

    def test_history_package_coverage_is_explicit(self):
        self.assertEqual(len(dgac.PACKAGES), 24)
        self.assertEqual(sum(6 for _ in dgac.PACKAGES), 144)
        self.assertNotIn((2014, 1), dgac.PACKAGES)
        self.assertNotIn((2015, 1), dgac.PACKAGES)
        self.assertIn((2017, 1), dgac.QUARANTINED_SOURCE_MONTHS)
        self.assertEqual(dgac.PACKAGES[(2015, 2)], "precipitacion-2o-semestre-2015")
        self.assertEqual(dgac.PACKAGES[(2026, 1)], "precipitacion-1er-semestre-2026")

    def test_legacy_resource_names_use_official_filename(self):
        resources = [
            {
                "name": "precipitaciones diarias por estacion",
                "format": "csv",
                "url": "https://datos.gob.cl/dataset/x/download/precipitacion0820151.csv",
            },
            {
                "name": "Precipitaciones Segundo semestre 2023",
                "format": "csv",
                "url": "https://datos.gob.cl/dataset/x/download/precipitacion_072023.csv",
            },
        ]
        self.assertEqual(dgac._resource_month(resources[0], 2015), 8)
        self.assertEqual(dgac._resource_month(resources[1], 2023), 7)
        self.assertIsNone(dgac._resource_month(resources[0], 2023))
        with self.assertRaisesRegex(dgac.SourceError, "externo"):
            dgac._resource_month({"url": "https://example.com/precipitacion_072023.csv"}, 2023)

    def test_conflicting_duplicate_month_fails_without_output(self):
        def get_package(_name):
            return {
                "license_id": "cc-by",
                "resources": [
                    {
                        "name": "Precipitacion_072015.csv",
                        "format": "csv",
                        "url": "https://datos.gob.cl/example/precipitacion_072015.csv",
                    },
                    {
                        "name": "Precipitacion_072015.csv",
                        "format": "csv",
                        "url": "https://datos.gob.cl/extra/precipitacion_072015.csv",
                    },
                    *[
                        {
                            "name": f"Precipitacion_{month:02d}2015.csv",
                            "format": "csv",
                            "url": f"https://datos.gob.cl/example/precipitacion_{month:02d}2015.csv",
                        }
                        for month in range(8, 13)
                    ],
                ],
            }

        def get_payload(url, *, retries=3):
            month = int(url.rsplit("/", 1)[-1][14:16])
            return sample_csv(2015, month, invalid="1.0" if "/extra/" in url else None)

        with tempfile.TemporaryDirectory() as tmp:
            outfile = Path(tmp) / "duplicados.csv"
            with (
                patch.object(dgac, "_package", side_effect=get_package),
                patch.object(dgac, "_request", side_effect=get_payload),
            ):
                with self.assertRaisesRegex(dgac.SourceError, "contenido distinto"):
                    dgac.harvest(outfile, start_year=2015, end_year=2015)
            self.assertFalse(outfile.exists())

    def test_invalid_year_range_fails(self):
        with self.assertRaisesRegex(dgac.SourceError, "Rango admitido"):
            dgac.harvest(Path("/no/escribir.csv"), start_year=2012)

    def test_invalid_source_does_not_publish_partial_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            outfile = Path(tmp) / "observaciones.csv"
            with patch.object(
                dgac, "_package", return_value={"license_id": "cc-zero", "resources": []}
            ):
                with self.assertRaises(dgac.SourceError):
                    dgac.harvest(outfile)
            self.assertFalse(outfile.exists())
            self.assertFalse(outfile.with_suffix(".metadata.json").exists())

    def test_production_wrapper_preserves_previous_snapshot_on_rejected_harvest(self):
        from src.extractors import precipitaciones_dgac_extractor as production

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "precipitaciones_dgac.csv"
            old_meta = out.with_suffix(".metadata.json")
            out.write_text("previous snapshot", encoding="utf-8")
            old_meta.write_text('{"retained":true}', encoding="utf-8")

            def incomplete(path):
                path.write_text("invalid snapshot", encoding="utf-8")
                path.with_suffix(".metadata.json").write_text("{}", encoding="utf-8")
                return {"months": 141, "record_count": 50}

            with patch.object(production, "harvest", side_effect=incomplete):
                with self.assertRaisesRegex(RuntimeError, "cobertura"):
                    production.extract(out)
            self.assertEqual(out.read_text(encoding="utf-8"), "previous snapshot")
            self.assertEqual(old_meta.read_text(encoding="utf-8"), '{"retained":true}')

    def test_semantic_validator_rejects_unlicensed_and_negative_rain(self):
        import polars as pl

        from src.validation import validate_precipitaciones_dgac

        data = pl.DataFrame(
            {
                "fecha": ["2017-01-01", "2017-01-01"],
                "id_estacion": ["180005", "180005"],
                "nombre_estacion": ["Arica", "Arica"],
                "latitud_dms": ["18 S", "18 S"],
                "altitud_m": [50.0, 50.0],
                "precipitacion_mm": [-2.0, 0.0],
                "url_fuente": ["https://datos.gob.cl/x"] * 2,
                "licencia_fuente": ["cc-nc", "cc-by"],
            }
        )
        status = validate_precipitaciones_dgac(data)
        self.assertEqual(status["status"], "error")
        self.assertTrue(any("duplicada" in x for x in status["errors"]))
        self.assertTrue(any("negativa" in x for x in status["errors"]))
        self.assertTrue(any("licencias" in x for x in status["errors"]))

    def test_publish_verifier_rejects_tampered_source_hash(self):
        from scripts.verify_dgac_publication import verify_and_write

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "dgac.csv"
            meta_path = root / "dgac.metadata.json"
            csv_path.write_text("tampered", encoding="utf-8")
            meta_path.write_text('{"sha256":"not-a-real-hash"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify_and_write(csv_path, meta_path, root / "out")
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()
