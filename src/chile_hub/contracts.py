"""Validación de datasets contra contratos JSON Schema.

Provee la función ``verify_dataset_contract()``, que valida un DataFrame de Polars
contra un contrato ``{dataset}.schema.json`` y retorna un dict con el resultado.

Migrado desde ``scripts/verify_pipeline.py`` para que la librería tenga esta
capacidad disponible en runtime.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl

__all__ = ["verify_dataset_contract", "contract_type"]


def contract_type(dtype: Any) -> str:
    """Convierte un tipo de columna Polars a su nombre canónico en JSON Schema.

    Args:
        dtype: Tipo de columna Polars (ej. pl.String, pl.Int32, pl.Float64).

    Returns:
        Nombre canónico: "string", "integer", "float", "date", "boolean".
    """
    dtype_name = str(dtype)
    if dtype_name == "String":
        return "string"
    if dtype_name in {
        "Int8",
        "Int16",
        "Int32",
        "Int64",
        "UInt8",
        "UInt16",
        "UInt32",
        "UInt64",
    }:
        return "integer"
    if dtype_name in {"Float32", "Float64"}:
        return "float"
    if dtype_name == "Date":
        return "date"
    if dtype_name == "Boolean":
        return "boolean"
    return dtype_name.lower()


def verify_dataset_contract(
    dataset_name: str,
    contract: dict[str, Any],
    df: pl.DataFrame,
    outputs: dict[str, str] | None = None,
    root_dir: str | Path | None = None,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """Valida un DataFrame contra un contrato JSON Schema de ChileHub.

    Args:
        dataset_name: Nombre del dataset (se coteja contra ``contract["dataset"]``).
        contract: Dict del contrato JSON Schema cargado.
        df: DataFrame de Polars a validar.
        outputs: Mapa ``{tipo: ruta_relativa}`` del catálogo (para verificar
            ``publish_outputs``). Opcional.
        root_dir: Directorio raíz del proyecto. Requerido si se pasa ``outputs``
            (para resolver las rutas relativas). Por defecto se infiere desde
            ``__file__``.
        strict: Si ``True``, las discrepancias en ``expected_record_count`` se
            reportan como error. Si ``False``, son solo advertencia.

    Returns:
        dict[str, Any]: Resultado de validación con ``dataset``, ``status``,
        ``errors`` y ``warnings``.
    """
    if root_dir is None:
        root_dir = Path(__file__).resolve().parents[2]
    root_dir = Path(root_dir)

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Coherencia del nombre del dataset
    if contract.get("dataset") != dataset_name:
        errors.append(
            f"El contrato tiene dataset='{contract.get('dataset')}', se esperaba '{dataset_name}'"
        )

    # 2. Columnas requeridas
    required_columns = contract.get("required_columns", [])
    missing_columns = [c for c in required_columns if c not in df.columns]
    if missing_columns:
        errors.append(f"Faltan columnas requeridas: {', '.join(missing_columns)}")

    # 3. Tipos de columna
    for column, expected_type in contract.get("column_types", {}).items():
        if column not in df.schema:
            errors.append(f"Columna '{column}' declarada en contract_type no existe en los datos")
            continue
        actual_type = contract_type(df.schema[column])
        if actual_type != expected_type:
            errors.append(f"Columna '{column}': tipo {actual_type}, se esperaba {expected_type}")

    # 4. Clave primaria
    primary_key = contract.get("primary_key", [])
    if primary_key:
        missing_key_columns = [c for c in primary_key if c not in df.columns]
        if missing_key_columns:
            errors.append(f"Columnas de clave primaria faltantes: {', '.join(missing_key_columns)}")
        else:
            # Valores nulos en PK
            null_mask = df.select(primary_key).null_count()
            if null_mask.sum_horizontal().item() > 0:
                errors.append(f"Clave primaria {primary_key} contiene valores nulos")
            # Unicidad de PK
            if df.select(primary_key).n_unique() != df.height:
                errors.append(
                    f"Clave primaria {primary_key} no es única "
                    f"({df.height - df.select(primary_key).n_unique()} duplicados)"
                )

    # 5. Columnas de ancho fijo (códigos CUT, etc.)
    for column, width in contract.get("fixed_width_columns", {}).items():
        if column not in df.schema:
            errors.append(f"Columna de ancho fijo '{column}' no existe en los datos")
            continue
        if contract_type(df.schema[column]) != "string":
            errors.append(
                f"Columna de ancho fijo '{column}' debe ser string "
                f"(tipo actual: {df.schema[column]})"
            )
        else:
            invalid_count = df.filter(
                pl.col(column).is_null() | (pl.col(column).str.len_chars() != width)
            ).height
            if invalid_count:
                errors.append(
                    f"Columna '{column}': {invalid_count} valores fuera del "
                    f"ancho esperado de {width} caracteres"
                )

    # 6. Conteo de registros esperado
    coverage_policy = contract.get("coverage_policy")
    expected_count = contract.get("expected_record_count")
    if expected_count is not None and df.height != expected_count:
        msg = (
            f"Registros: {df.height}, se esperaban {expected_count} "
            f"(coverage_policy={coverage_policy})"
        )
        if coverage_policy == "full" and strict:
            errors.append(msg)
        else:
            warnings.append(msg)

    # 7. Outputs publicables
    if outputs:
        for output_type in contract.get("publish_outputs", []):
            relative_path = outputs.get(output_type)
            if not relative_path:
                errors.append(f"El catálogo no tiene entrada para output '{output_type}'")
            else:
                output_path = root_dir / relative_path
                if not output_path.exists():
                    errors.append(f"Output '{output_type}' no existe: {relative_path}")

    status = "ok" if not errors else "error"
    return {
        "dataset": dataset_name,
        "status": status,
        "errors": errors,
        "warnings": warnings,
    }
