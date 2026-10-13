"""Helpers compartidos de validación (plan 135)."""

import polars as pl


def _missing_columns(df: pl.DataFrame, columns: list[str]) -> list[str]:
    return [column for column in columns if column not in df.columns]


def _duplicate_count(df: pl.DataFrame, columns: list[str]) -> int:
    if df.height == 0:
        return 0
    return df.height - df.select(columns).unique().height


def _add_expected_warning(warnings: list[str], expected_warnings: list[str], message: str) -> None:
    """Registra un warning que describe diseño confirmado, no degradación.

    El mensaje entra en ``warnings`` como cualquier otro — el registro sigue
    siendo completo y transparente — y además en ``expected_warnings``, que es
    el subconjunto que ``build_degradation`` descuenta para calcular los
    warnings *accionables* (ver ADR-014).

    La declaración vive junto a la regla que emite el warning, nunca en el
    consumidor: clasificar por texto en el consumidor se rompe la primera vez
    que alguien reformula el mensaje.
    """
    warnings.append(message)
    expected_warnings.append(message)


def _invalid_fixed_length_count(df: pl.DataFrame, column: str, length: int) -> int:
    return df.filter(pl.col(column).cast(pl.String).str.len_chars() != length).height


def _unknown_codes(df: pl.DataFrame, column: str, valid_codes: list[str] | None) -> list[str]:
    if valid_codes is None:
        return []
    return sorted(set(df[column].drop_nulls().cast(pl.String).to_list()) - set(valid_codes))


def _negative_numeric_count(df: pl.DataFrame, columns: list[str]) -> int:
    count = 0
    for column in columns:
        count += df.filter(pl.col(column).is_not_null() & (pl.col(column) < 0)).height
    return count


def _percentage_out_of_bounds_count(df: pl.DataFrame, columns: list[str]) -> int:
    count = 0
    for column in columns:
        count += df.filter(
            pl.col(column).is_not_null() & ((pl.col(column) < 0) | (pl.col(column) > 100))
        ).height
    return count


def _expected_dv_vectorized(bases: pl.Series) -> pl.Series:
    """Calcula el dígito verificador Módulo 11 de forma vectorizada.

    ``bases`` deben ser strings numéricos de 7 u 8 dígitos (ya validados).
    El algoritmo (Módulo 11):
      - Desde el dígito más a la derecha, pesos cíclicos 2,3,4,5,6,7,2,3,...
      - Suma ponderada, resto módulo 11, DV = 11 - resto
      - 11 -> "0", 10 -> "k", else -> str(resto)
    """
    padded = bases.str.zfill(8)
    # Para un string de 8 chars right-aligned, pesos por posición (0=izquierda):
    weights = [3, 2, 7, 6, 5, 4, 3, 2]

    frame = padded.to_frame("b")
    weighted = pl.lit(0)
    for offset, w in enumerate(weights):
        digit = pl.col("b").str.slice(offset, 1).cast(pl.Int64)
        weighted = weighted + digit * w

    r = weighted % 11
    dv = 11 - r
    expr = (
        pl.when(dv == 11)
        .then(pl.lit("0"))
        .when(dv == 10)
        .then(pl.lit("k"))
        .otherwise(dv.cast(pl.String))
    )
    return frame.select(expr.alias("dv"))["dv"]


def _validate_ruts_column(rut_series: pl.Series) -> tuple[int, int]:
    """Valida formato y dígito verificador de RUTs.

    Retorna (format_bad_count, dv_bad_count):
    - format_bad_count: RUTs que no cumplen el formato XX.XXX.XXX-X
    - dv_bad_count: RUTs con formato válido pero dígito verificador incorrecto
    """
    # Limpiar: rellenar nulos con cadena vacía, eliminar puntos, recortar espacios
    filled = rut_series.fill_null("")
    cleaned = filled.str.replace_all(r"\.", "").str.strip_chars()

    # Fase 1: verificar formato básico (Polars vectorizado)
    # Los nulos se excluyen aquí: ya son reportados como error por validate_empresas
    has_valid_format = cleaned.str.contains(r"^\d{7,8}-[\dkK]$")
    is_not_null = rut_series.is_not_null()
    format_bad = (~has_valid_format) & is_not_null
    format_bad_count = int(format_bad.sum())

    # Fase 2: validar dígito verificador solo para RUTs con buen formato
    valid_ruts = cleaned.filter(has_valid_format)
    if valid_ruts.len() == 0:
        return format_bad_count, 0

    # Extraer base numérica y DV declarado
    bases = valid_ruts.str.replace(r"-[\dkK]$", "")
    declared_dvs = valid_ruts.str.replace(r"^\d{7,8}-", "").str.to_lowercase()

    # Calcular DV esperado para cada base (Polars vectorizado)
    expected_dvs = _expected_dv_vectorized(bases)

    dv_bad = declared_dvs != expected_dvs
    dv_bad_count = int(dv_bad.sum())

    return format_bad_count, dv_bad_count
