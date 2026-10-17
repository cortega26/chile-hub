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
                    "url": "https://datos.gob.cl/x",
                }
            ]
        }
        with self.assertRaisesRegex(dgac.SourceError, "Faltan CSV"):
            dgac.resources_for_package(package, 2025, range(7, 13))
        duplicated = {"resources": [*package["resources"], *package["resources"]]}
        with self.assertRaisesRegex(dgac.SourceError, "Dos recursos"):
            dgac.resources_for_package(duplicated, 2025, range(7, 8))

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
                        "url": f"https://datos.gob.cl/example/{month:02d}{year}.csv",
                    }
                    for month in months
                ],
            }

        def request(url, *, retries=3):
            token = url.rsplit("/", 1)[-1].removesuffix(".csv")
            month, year = int(token[:2]), int(token[2:])
            return sample_csv(year, month)

        with tempfile.TemporaryDirectory() as tmp:
            outfile = Path(tmp) / "observaciones.csv"
            with (
                patch.object(dgac, "_package", side_effect=get_package),
                patch.object(dgac, "_request", side_effect=request),
            ):
                meta = dgac.harvest(outfile)
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


if __name__ == "__main__":
    unittest.main()
