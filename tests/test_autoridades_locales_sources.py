"""Deterministic source-fallback contracts for local-authority acquisition.

BCN SIIT remains authoritative for the mayor's name. Wikipedia may enrich the
mandate start date, or supply a name only when BCN has none. No live HTTP.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.extractors import autoridades_locales_extractor as local


class LocalAuthoritySourceFallbackTests(unittest.TestCase):
    def test_bcn_name_wins_and_wikipedia_date_matches_accented_comuna(self):
        title = "Anexo:Alcaldes de Ñuñoa"
        with (
            patch.object(local, "_load_comunas_lookup", return_value={"nunoa": ("13120", "13")}),
            patch.object(
                local,
                "fetch_alcaldes_bcn",
                return_value=[{"comuna": "nunoa", "nombre": "Titular BCN", "periodo_inicio": None}],
            ),
            patch.object(local, "fetch_alcalde_titles", return_value=[title]),
            patch.object(
                local,
                "fetch_alcaldes_wikitext",
                return_value={
                    title: "| titular = [[Otra persona]]\n| inicio = {{fecha|6|12|2024}}\n"
                },
            ),
        ):
            rows = local.fetch_alcaldes()

        self.assertEqual(
            rows,
            [{"comuna": "nunoa", "nombre": "Titular BCN", "periodo_inicio": "2024-12-06"}],
        )

    def test_wikipedia_supplies_name_only_for_bcn_vacancy(self):
        title = "Anexo:Alcaldes de Arica"
        with (
            patch.object(
                local,
                "_load_comunas_lookup",
                return_value={"arica": ("15101", "15"), "iquique": ("01101", "01")},
            ),
            patch.object(
                local,
                "fetch_alcaldes_bcn",
                return_value=[
                    {"comuna": "arica", "nombre": None, "periodo_inicio": None},
                    {"comuna": "iquique", "nombre": "Titular BCN", "periodo_inicio": None},
                ],
            ),
            patch.object(local, "fetch_alcalde_titles", return_value=[title]),
            patch.object(
                local,
                "fetch_alcaldes_wikitext",
                return_value={title: "| titular = [[Titular WP]]\n"},
            ),
        ):
            rows = local.fetch_alcaldes()

        by_comuna = {row["comuna"]: row for row in rows}
        self.assertEqual(set(by_comuna), {"arica", "iquique"})
        self.assertEqual(by_comuna["arica"]["nombre"], "Titular WP")
        self.assertEqual(by_comuna["iquique"]["nombre"], "Titular BCN")

    def test_wikipedia_outage_keeps_official_bcn_rows(self):
        with (
            patch.object(local, "_load_comunas_lookup", return_value={"arica": ("15101", "15")}),
            patch.object(
                local,
                "fetch_alcaldes_bcn",
                return_value=[{"comuna": "arica", "nombre": "Titular BCN", "periodo_inicio": None}],
            ),
            patch.object(local, "fetch_alcalde_titles", side_effect=OSError("wiki offline")),
            patch.object(local, "fetch_alcaldes_wikitext") as fetch_text,
        ):
            rows = local.fetch_alcaldes()

        self.assertEqual(
            rows, [{"comuna": "arica", "nombre": "Titular BCN", "periodo_inicio": None}]
        )
        fetch_text.assert_not_called()

    def test_total_bcn_outage_falls_back_to_wikipedia(self):
        title = "Anexo:Alcaldes de Arica"
        with (
            patch.object(local, "_load_comunas_lookup", return_value={"arica": ("15101", "15")}),
            patch.object(local, "fetch_alcaldes_bcn", side_effect=OSError("BCN offline")),
            patch.object(local, "fetch_alcalde_titles", return_value=[title]),
            patch.object(
                local,
                "fetch_alcaldes_wikitext",
                return_value={title: "| titular = [[Titular WP]]\n"},
            ),
        ):
            rows = local.fetch_alcaldes()

        self.assertEqual(
            rows, [{"comuna": "Arica", "nombre": "Titular WP", "periodo_inicio": None}]
        )

    def test_both_sources_offline_do_not_invent_authorities(self):
        with (
            patch.object(local, "_load_comunas_lookup", return_value={"arica": ("15101", "15")}),
            patch.object(local, "fetch_alcaldes_bcn", side_effect=OSError("BCN offline")),
            patch.object(local, "fetch_alcalde_titles", side_effect=OSError("wiki offline")),
        ):
            self.assertEqual(local.fetch_alcaldes(), [])

    def test_missing_comuna_lookup_short_circuits_all_requests(self):
        with (
            patch.object(local, "_load_comunas_lookup", return_value={}),
            patch.object(local, "fetch_alcaldes_bcn") as bcn,
            patch.object(local, "fetch_alcalde_titles") as wikipedia,
        ):
            self.assertEqual(local.fetch_alcaldes(), [])

        bcn.assert_not_called()
        wikipedia.assert_not_called()

    def test_bcn_batch_skips_invalid_codes_and_preserves_missing_names(self):
        lookup = {
            "arica": ("15101", "15"),
            "santiago": ("13101", "13"),
            "chile": ("00000", "00"),
            "invalid": ("7", "01"),
        }

        def resolve(codigo):
            return "Titular BCN" if codigo == "15101" else None

        with patch.object(local, "fetch_alcalde_bcn", side_effect=resolve) as fetch:
            rows = local.fetch_alcaldes_bcn(lookup, max_workers=2)

        by_comuna = {row["comuna"]: row for row in rows}
        self.assertEqual(set(by_comuna), {"arica", "santiago"})
        self.assertEqual(by_comuna["arica"]["nombre"], "Titular BCN")
        self.assertIsNone(by_comuna["santiago"]["nombre"])
        self.assertEqual({call.args[0] for call in fetch.call_args_list}, {"15101", "13101"})

    def test_bcn_missing_placeholder_and_network_error_return_none(self):
        for cell in ("Vacante", "No Disponible", " "):
            response = MagicMock(text=f"<td>Alcalde</td><td>{cell}</td>")
            with (
                self.subTest(cell=cell),
                patch.object(local, "fetch_with_retry", return_value=response),
            ):
                self.assertIsNone(local.fetch_alcalde_bcn("15101"))

        with patch.object(local, "fetch_with_retry", side_effect=OSError("offline")):
            self.assertIsNone(local.fetch_alcalde_bcn("15101"))
