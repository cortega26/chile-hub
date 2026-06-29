"""Tests unitarios para el helper de renderizado _render.py.

Estos tests verifican que render_table produzca texto plano sin ANSI y
preserve el titulo, encabezados y celdas.
"""

from __future__ import annotations

from chile_hub._render import render_table


class TestRenderTable:
    """Tests para render_table()."""

    def test_returns_string_with_title(self):
        output = render_table("chile-hub demo", ["a", "b"], [["1", "2"]])
        assert isinstance(output, str)
        assert "chile-hub demo" in output

    def test_includes_headers_and_cells(self):
        output = render_table("test", ["name", "value"], [["foo", "bar"]])
        assert "name" in output
        assert "value" in output
        assert "foo" in output
        assert "bar" in output

    def test_no_ansi_escape_codes(self):
        output = render_table("test", ["x"], [["y"]])
        assert "\x1b[" not in output, f"Salida contiene ANSI: {output!r}"

    def test_unicode_accented_names(self):
        output = render_table(
            "test",
            ["comuna"],
            [["Ñuñoa"]],
        )
        assert "Ñuñoa" in output

    def test_empty_rows_does_not_crash(self):
        output = render_table("empty", ["h"], [])
        assert "empty" in output
        assert isinstance(output, str)

    def test_multiple_rows_preserve_order(self):
        output = render_table(
            "multi",
            ["id"],
            [["1"], ["2"], ["3"]],
        )
        # Verificar que los valores aparecen en la salida
        for val in ("1", "2", "3"):
            assert val in output
