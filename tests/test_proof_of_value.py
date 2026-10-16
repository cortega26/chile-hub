"""Prueba offline del benchmark; no requiere acceso a fuentes ni dependencias externas."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "proof_of_value.py"
SPEC = importlib.util.spec_from_file_location("proof_of_value", SCRIPT)
assert SPEC and SPEC.loader
proof = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(proof)


def cut(i: int) -> str:
    return f"{i:05d}"


class ValueProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.directory = Path(self.tempdir.name)
        codes = [cut(i) for i in (1101, 1102, 1103)]
        commons = [
            {"codigo_comuna": c, "codigo_region": "01", "nombre_comuna": f"Comuna {i}"}
            for i, c in enumerate(codes)
        ]
        rows = {
            "comunas": commons,
            "censo_comunal": [
                {"codigo_comuna": c, "poblacion_censada": 100 + i, "poblacion_65_mas": 10 + i}
                for i, c in enumerate(codes)
            ],
            "censo_hogares_viviendas": [
                {"codigo_comuna": c, "hogares_censados": 20 + i, "viviendas_censadas": 30 + i}
                for i, c in enumerate(codes)
            ],
            "perfil_territorial_comunal": [
                {**c, "poblacion_censada": 100 + i} for i, c in enumerate(commons)
            ],
            "pobreza_comunal": [
                {"codigo_comuna": c, "dimension": "ingresos", "anio": 2022, "tasa": 11.5 + i}
                for i, c in enumerate(codes[:2])
            ] + [
                {"codigo_comuna": c, "dimension": "multidimensional", "anio": 2022, "tasa": 20.0}
                for c in codes[:2]
            ],
        }
        self.rows = rows
        self.write_data()

    def write_data(self) -> None:
        for name, rows in self.rows.items():
            (self.directory / f"{name}.json").write_text(json.dumps(rows), encoding="utf-8")

    def test_coverage_and_provenance(self) -> None:
        report = proof.run_proof(self.directory, runs=2, expected_communes=3)
        self.assertEqual(len(report["cases"]), 3)
        self.assertEqual([c["resultado"]["comunas_cruzadas"] for c in report["cases"]], [3, 3, 2])
        self.assertEqual(report["cases"][2]["resultado"]["cobertura_pct"], 66.67)
        self.assertEqual(report["cases"][2]["resultado"]["cut_sin_cruce"], ["01103"])
        self.assertEqual(len(report["sources"]), 5)
        self.assertTrue(all(len(a["sha256"]) == 64 for a in report["sources"]))

    def test_determinism_of_results(self) -> None:
        before = proof.run_proof(self.directory, runs=1, expected_communes=3)
        after = proof.run_proof(self.directory, runs=3, expected_communes=3)
        self.assertEqual(
            [c["resultado_sha256"] for c in before["cases"]],
            [c["resultado_sha256"] for c in after["cases"]],
        )

    def test_reject_duplicate_cut(self) -> None:
        self.rows["comunas"].append(dict(self.rows["comunas"][0]))
        self.write_data()
        with self.assertRaisesRegex(ValueError, "duplicado"):
            proof.run_proof(self.directory, runs=1, expected_communes=3)

    def test_reject_numeric_cut(self) -> None:
        self.rows["censo_comunal"][0]["codigo_comuna"] = 1101
        self.write_data()
        with self.assertRaisesRegex(ValueError, "CUT inválido"):
            proof.run_proof(self.directory, runs=1, expected_communes=3)

    def test_reject_missing_file(self) -> None:
        (self.directory / "pobreza_comunal.json").unlink()
        with self.assertRaisesRegex(ValueError, "No existe artefacto"):
            proof.run_proof(self.directory, runs=1, expected_communes=3)

    def test_reject_unexpected_cardinality(self) -> None:
        with self.assertRaisesRegex(ValueError, "esperadas 346"):
            proof.run_proof(self.directory, runs=1)

    def test_reject_mutating_published_artifacts(self) -> None:
        with patch.object(proof, "PROJECT_ROOT", self.directory):
            data_dir = self.directory / "data" / "normalized"
            data_dir.mkdir(parents=True)
            with patch.object(proof, "run_proof", return_value={"cases": []}):
                self.assertEqual(proof.main(["--output", str(data_dir / "proof.json")]), 2)


if __name__ == "__main__":
    unittest.main()
