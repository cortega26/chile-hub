"""Esquema canónico compartido del carril autoridades (plan 133a, auditoría 2026-10-13).

`SCHEMA` era **idéntico** en `autoridades_electas_extractor.py` y
`autoridades_locales_extractor.py` (16 columnas, mismas claves y tipos). Una
sola definición elimina la deriva silenciosa entre ambas salidas de staging:
un cambio de esquema que toque solo una copia publicaría contratos distintos.

No incluye `REUSE_POLICY` a propósito: divergen (CC-BY vs CC-BY-SA, datasets
segregados por licencia — ver AGENTS §6).
"""

import polars as pl

# Columnas canónicas del carril autoridades (diputados, senadores,
# gobernadores regionales y alcaldes comparten esquema de staging).
SCHEMA: dict[str, type[pl.DataType]] = {
    "id_autoridad": pl.String,
    "nombre": pl.String,
    "cargo": pl.String,
    "institucion": pl.String,
    "partido": pl.String,
    "pacto": pl.String,
    "distrito_electoral": pl.String,
    "circunscripcion_senatorial": pl.String,
    "codigo_comuna": pl.String,
    "codigo_region": pl.String,
    "periodo_inicio": pl.String,
    "periodo_fin": pl.String,
    "estado_mandato": pl.String,
    "fuente": pl.String,
    "url_fuente": pl.String,
    "fecha_consulta": pl.String,
}
