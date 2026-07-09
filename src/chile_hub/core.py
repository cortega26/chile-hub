import argparse
import functools
import importlib.metadata
import json
import sys
from datetime import datetime, timezone
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Literal

import polars as pl
import requests

from ._render import render_table
from .data_manager import ChileHubDataManager
from .datasets import Dataset
from .exceptions import (
    ChileHubDataError,
    ChileHubDatasetError,
    ChileHubError,
    ChileHubExampleError,
    ChileHubOutputError,
)
from .pipeline_status_utils import (
    compute_freshness,
    compute_top_issue,
    format_top_issue_summary,
)

UTC = timezone.utc

ROOT_DIR = Path(__file__).resolve().parents[2]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
DATASET_CATALOG_PATH = NORMALIZED_DIR / "dataset_catalog.json"


def _resolve_dataset_name(dataset_name: str | Dataset) -> str:
    """Convierte un dataset_name a string, validando contra el enum ``Dataset``.

    Acepta tanto strings como miembros del enum ``Dataset``. Si se pasa un
    string que no es un dataset válido, lanza ``ChileHubDatasetError`` con
    sugerencia.
    """
    if isinstance(dataset_name, Dataset):
        return dataset_name.value
    try:
        return Dataset.from_string(dataset_name).value
    except ValueError as exc:
        raise ChileHubDatasetError(str(exc)) from exc


def _format_available(values: list[str], requested: str | None = None) -> str:
    available = ", ".join(values) if values else "none"
    if not requested:
        return f"Disponibles: {available}"
    matches = get_close_matches(requested, values, n=1)
    if matches:
        return f"Disponibles: {available}. Quizas quisiste decir '{matches[0]}'."
    return f"Disponibles: {available}"


def _print_result(result, fmt="json", output=None):
    """Imprime un resultado dict/list en el formato solicitado."""
    if output:
        import polars as pl

        if isinstance(result, pl.DataFrame):
            if output == "csv":
                result.write_csv(sys.stdout)
            elif output == "parquet":
                result.write_parquet(sys.stdout.buffer)
            elif output == "json":
                result.write_json(sys.stdout)  # type: ignore[arg-type]  # TextIO es IOBase; falso positivo en stubs de Polars
            return
    if fmt == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # table: convertir dict a string formateado
        if isinstance(result, dict):
            for k, v in result.items():
                print(f"{k}: {v}")
        elif isinstance(result, list):
            for item in result:
                if isinstance(item, dict):
                    print(json.dumps(item, ensure_ascii=False, indent=2))
                else:
                    print(item)
        else:
            print(result)


def _output_dataframe(df, output, fmt):
    """Escribe un DataFrame a stdout o archivo según output y fmt."""
    import sys

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if output.endswith(".csv"):
            df.write_csv(out_path)
        elif output.endswith(".parquet"):
            df.write_parquet(out_path)
        elif output.endswith(".json"):
            df.write_json(out_path)
        else:
            raise ValueError(
                f"Formato de archivo no soportado: {output}. Use .csv, .parquet o .json"
            )
        print(f"Escrito en {output}")
    elif fmt == "json":
        df.write_json(sys.stdout)
    else:
        print(df)


class ChileHub:
    def __init__(
        self,
        catalog_path: str | Path | None = None,
        *,
        data_dir: str | Path | None = None,
        data_version: str = "latest",
        auto_update: bool = True,
    ) -> None:
        if catalog_path is not None and data_dir is not None:
            raise ValueError("Use catalog_path or data_dir, not both.")

        if catalog_path is not None:
            self.catalog_path = Path(catalog_path)
        elif data_dir is not None:
            self.catalog_path = Path(data_dir) / "dataset_catalog.json"
        elif DATASET_CATALOG_PATH.exists():
            self.catalog_path = DATASET_CATALOG_PATH
        else:
            manager = ChileHubDataManager(data_version=data_version)
            self.catalog_path = (
                manager.ensure_data_dir(auto_update=auto_update) / "dataset_catalog.json"
            )

        self.normalized_dir = self.catalog_path.resolve().parent
        self.root_dir = self.normalized_dir.parents[1]
        self.catalog = self._load_catalog()
        self._df_cache: dict[str, pl.DataFrame] = {}

    def _load_catalog(self) -> dict[str, Any]:
        try:
            with self.catalog_path.open("r", encoding="utf-8") as f:
                return json.load(f)  # type: ignore[no-any-return]  # json.load → dict en runtime
        except FileNotFoundError:
            raise ChileHubDataError(
                f"Catálogo de datasets no encontrado en {self.catalog_path}. "
                f"Usa ChileHub() sin argumentos para descargar el bundle automáticamente, "
                f"o asegúrate de que el directorio '{self.catalog_path.parent}' contiene "
                f"los datos normalizados (ejecuta 'make build' si estás en desarrollo)."
            )

    def _load_json_artifact(self, filename: str) -> dict[str, Any]:
        with (self.normalized_dir / filename).open("r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]

    @functools.lru_cache(maxsize=1)
    def _load_artifact_manifest(self) -> dict[str, Any]:
        return self._load_json_artifact("artifact_manifest.json")

    @functools.lru_cache(maxsize=1)
    def _load_hub_health(self) -> dict[str, Any]:
        return self._load_json_artifact("hub_health.json")

    @functools.lru_cache(maxsize=1)
    def _load_hub_status(self) -> dict[str, Any]:
        return self._load_json_artifact("hub_status.json")

    @functools.lru_cache(maxsize=1)
    def _load_dataset_status(self) -> dict[str, Any]:
        return self._load_json_artifact("dataset_status.json")

    @functools.lru_cache(maxsize=1)
    def _load_dataset_changelog(self) -> dict[str, Any]:
        return self._load_json_artifact("dataset_changelog.json")

    @functools.lru_cache(maxsize=1)
    def _load_hub_bundle(self) -> dict[str, Any]:
        return self._load_json_artifact("hub_bundle.json")

    @functools.lru_cache(maxsize=1)
    def _load_redistribution_report(self) -> dict[str, Any]:
        return self._load_json_artifact("redistribution_report.json")

    @functools.lru_cache(maxsize=1)
    def _load_provenance_report(self) -> dict[str, Any]:
        return self._load_json_artifact("provenance_report.json")

    @functools.lru_cache(maxsize=1)
    def _load_drift_report(self) -> dict[str, Any]:
        return self._load_json_artifact("drift_report.json")

    @functools.lru_cache(maxsize=1)
    def _load_source_readiness(self) -> dict[str, Any]:
        return self._load_json_artifact("source_readiness.json")

    @functools.lru_cache(maxsize=1)
    def _load_dataset_quality(self) -> dict[str, Any]:
        return self._load_json_artifact("dataset_quality.json")

    @staticmethod
    def _status_rank(status: str) -> int:
        return {"ok": 0, "warn": 1, "error": 2}.get(status, 1)

    @classmethod
    def _max_status(cls, *statuses: str) -> str:
        filtered = [status for status in statuses if status]
        if not filtered:
            return "unknown"
        return max(filtered, key=cls._status_rank)

    def top_issue(self) -> dict[str, Any] | None:
        provenance_by_dataset = {
            entry.get("dataset"): entry for entry in self.provenance().get("datasets", [])
        }
        drift_by_dataset = {
            entry.get("dataset"): entry for entry in self.drift().get("datasets", [])
        }
        freshness_by_dataset = {
            entry.get("dataset"): entry for entry in self.freshness_audit().get("datasets", [])
        }
        entries = []
        for entry in self.summary():
            dataset_name = entry.get("dataset")
            freshness_entry = freshness_by_dataset.get(dataset_name, {})
            provenance = provenance_by_dataset.get(dataset_name, {})
            drift = drift_by_dataset.get(dataset_name, {})
            current_freshness_status = freshness_entry.get("current_freshness_status", "unknown")
            entries.append(
                {
                    "dataset": dataset_name,
                    "warning_count": entry.get("warning_count", 0),
                    "freshness_status": current_freshness_status,
                    "build_freshness_status": entry.get("freshness_status"),
                    "current_freshness_status": current_freshness_status,
                    "drift_status": entry.get("drift_status"),
                    "degradation_status": entry.get("degradation_status"),
                    "source_detail": provenance.get("source_detail", "unknown"),
                    "diagnostic_summary": drift.get(
                        "diagnostic_summary",
                        provenance.get("diagnostic_summary", "Sin observaciones operativas."),
                    ),
                    "recommended_action": drift.get("recommended_action", "Ninguna."),
                }
            )

        return compute_top_issue(entries)  # type: ignore[no-any-return]  # dict en runtime

    def top_issue_table(self) -> str:
        top_issue = self.top_issue()
        if not top_issue:
            return "chile-hub top issue\n\nSin top issue activo.\n"

        rows = [
            ["dataset", top_issue.get("dataset", "unknown")],
            ["attention_priority", str(top_issue.get("attention_priority", "unknown"))],
            ["build_freshness_status", top_issue.get("build_freshness_status", "unknown")],
            ["current_freshness_status", top_issue.get("current_freshness_status", "unknown")],
            ["drift_status", top_issue.get("drift_status", "unknown")],
            ["degradation_status", top_issue.get("degradation_status", "unknown")],
            ["warning_count", str(top_issue.get("warning_count", 0))],
            ["source_detail", top_issue.get("source_detail", "unknown")],
            ["diagnostic_summary", top_issue.get("diagnostic_summary", "unknown")],
            ["recommended_action", top_issue.get("recommended_action", "unknown")],
        ]
        return render_table("chile-hub top issue", ["key", "value"], rows)

    def list_datasets(self) -> list[str]:
        return [entry["dataset"] for entry in self.catalog.get("datasets", [])]

    def get_dataset(self, dataset_name: str | Dataset) -> dict[str, Any]:
        dataset_name = _resolve_dataset_name(dataset_name)
        for entry in self.catalog.get("datasets", []):
            if entry["dataset"] == dataset_name:
                return entry  # type: ignore[no-any-return]  # dict[str, Any] en runtime
        raise ChileHubDatasetError(
            f"Dataset '{dataset_name}' no existe. {_format_available(self.list_datasets(), dataset_name)}"
        )

    def get_output_path(self, dataset_name: str | Dataset, output_type: str = "parquet") -> Path:
        dataset_name = _resolve_dataset_name(dataset_name)
        dataset = self.get_dataset(dataset_name)
        # Resolver alias: si el dataset apunta a otro, usar el canónico
        alias_for = dataset.get("alias_for")
        if alias_for:
            return self.get_output_path(alias_for, output_type)
        outputs = dataset.get("outputs", {})
        if output_type not in outputs:
            available_outputs = sorted(outputs.keys())
            raise ChileHubOutputError(
                f"Output '{output_type}' no existe para '{dataset_name}'. "
                f"{_format_available(available_outputs, output_type)}"
            )
        return self.root_dir / outputs[output_type]  # type: ignore[no-any-return]  # Path en runtime

    def load_polars(self, dataset_name: str | Dataset, validate: bool = False) -> pl.DataFrame:
        """Carga un dataset como DataFrame de Polars.

        Args:
            dataset_name: Nombre del dataset (ej. "comunas", "indicadores").
            validate: Si ``True``, ejecuta ``validate_dataset()`` antes de retornar.
                Lanza ``ChileHubDataError`` si la validación falla.

        Returns:
            DataFrame de Polars con los datos del dataset.

        Raises:
            ChileHubDatasetError: Si el dataset no existe o el archivo es ilegible.
            ChileHubDataError: Si ``validate=True`` y la validación encuentra errores.
        """
        dataset_name = _resolve_dataset_name(dataset_name)
        if not validate or dataset_name not in self._df_cache:
            path = self.get_output_path(dataset_name, "parquet")
            try:
                df = pl.read_parquet(path)
            except FileNotFoundError:
                raise ChileHubDatasetError(
                    f"Archivo Parquet no encontrado para '{dataset_name}': {path}"
                )
            except Exception as exc:
                raise ChileHubDatasetError(f"Error al leer Parquet para '{dataset_name}': {exc}")
            self._df_cache[dataset_name] = df

        if validate:
            result = self.validate_dataset(dataset_name)
            if result["status"] == "error":
                raise ChileHubDataError(
                    f"Validación fallida para '{dataset_name}': {'; '.join(result['errors'])}"
                )

        return self._df_cache[dataset_name]

    def cross_view(
        self,
        datasets: list[str | Dataset],
        on: str = "codigo_comuna",
        how: Literal["inner", "left", "right", "full", "semi", "anti", "cross", "outer"] = "left",
    ) -> pl.DataFrame:
        """Retorna un cruce predefinido de datasets vinculados por clave territorial.

        Args:
            datasets: Lista de nombres de datasets a cruzar (ej. ["comunas", "censo_comunal"]).
            on: Clave de join (default: "codigo_comuna").
            how: Tipo de join (default: "left").

        Returns:
            DataFrame de Polars con el cruce de todos los datasets.

        Raises:
            ChileHubDatasetError: Si se pasan menos de 2 datasets.
        """
        if len(datasets) < 2:
            raise ChileHubDatasetError(
                f"cross_view requiere al menos 2 datasets. Recibido: {len(datasets)}"
            )

        dfs = []
        for name in datasets:
            df = self.load_polars(name)
            # Prefijar columnas no-clave con el nombre del dataset para evitar colisiones
            cols_to_prefix = [c for c in df.columns if c != on]
            df = df.select([pl.col(on)] + [pl.col(c).alias(f"{name}_{c}") for c in cols_to_prefix])
            dfs.append(df)

        result = dfs[0]
        for df in dfs[1:]:
            result = result.join(df, on=on, how=how)
        return result

    def validate_dataset(self, dataset_name: str | Dataset) -> dict:
        """Valida los datos publicados del hub contra su contrato JSON Schema.

        Carga el dataset desde Parquet y lo coteja contra el contrato en
        ``contracts/datasets/{dataset_name}.schema.json``. Retorna un dict
        con ``status``, ``errors`` y ``warnings``.

        Args:
            dataset_name: Nombre del dataset (ej. ``"comunas"``).

        Returns:
            Dict con:
            - ``dataset``: nombre del dataset validado.
            - ``status``: ``"ok"`` o ``"error"``.
            - ``errors``: lista de errores de validación.
            - ``warnings``: lista de advertencias.

        Raises:
            ChileHubDatasetError: Si no existe contrato o dataset.
        """
        dataset_name = _resolve_dataset_name(dataset_name)
        from .contracts import verify_dataset_contract

        contract_path = self.root_dir / "contracts" / "datasets" / f"{dataset_name}.schema.json"
        if not contract_path.exists():
            raise ChileHubDatasetError(
                f"No existe contrato de schema para '{dataset_name}'. "
                f"Datasets disponibles: {self.list_datasets()}"
            )

        with contract_path.open("r", encoding="utf-8") as f:
            contract = json.load(f)

        df = self.load_polars(dataset_name)
        catalog_entry = self.get_dataset(dataset_name)
        outputs = catalog_entry.get("outputs", {}) if catalog_entry else {}

        return verify_dataset_contract(
            dataset_name,
            contract,
            df,
            outputs=outputs,
            root_dir=self.root_dir,
        )

    def validate_user_data(self, df: pl.DataFrame, dataset_name: str | Dataset) -> dict:
        """Valida un DataFrame de usuario contra el contrato de schema del dataset.

        Usa los archivos de contrato en contracts/datasets/*.schema.json, que definen
        required_columns, column_types, primary_key y expected_record_count.

        Args:
            df: DataFrame de Polars a validar.
            dataset_name: Nombre del dataset de referencia (ej. "comunas").

        Returns:
            Dict con:
            - status: "ok" si pasa todas las validaciones, "error" si falla alguna.
            - errors: lista de strings con mensajes de error (vacía si status=="ok").
            - warnings: lista de strings con advertencias no bloqueantes.
            - schema_used: ruta absoluta del schema usado.

        Raises:
            ChileHubDatasetError: Si no existe contrato para el dataset solicitado.
        """
        dataset_name = _resolve_dataset_name(dataset_name)
        schema_path = ROOT_DIR / "contracts" / "datasets" / f"{dataset_name}.schema.json"
        if not schema_path.exists():
            raise ChileHubDatasetError(
                f"No existe contrato de schema para '{dataset_name}'. "
                f"Datasets disponibles: {self.list_datasets()}"
            )

        import json as json_module

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json_module.load(f)

        errors = []
        warnings = []

        # 1. Validar columnas requeridas (required_columns)
        required_cols = schema.get("required_columns", [])
        df_cols = df.columns
        missing = [c for c in required_cols if c not in df_cols]
        if missing:
            errors.append(f"Columnas requeridas faltantes: {missing}")

        # 2. Validar tipos (column_types)
        column_types = schema.get("column_types", {})
        type_map = {
            "string": ["String", "Utf8", "str"],
            "integer": ["Int64", "Int32", "Int16", "Int8", "UInt32", "UInt16"],
            "number": ["Float64", "Float32"],
            "boolean": ["Boolean"],
            "date": ["Date"],
        }
        for col, expected_type in column_types.items():
            if col not in df_cols:
                continue
            actual_dtype = str(df[col].dtype)
            expected_names = type_map.get(expected_type, [expected_type])
            if actual_dtype not in expected_names:
                errors.append(
                    f"Columna '{col}': se esperaba {expected_type}, se encontró {actual_dtype}"
                )

        # 3. Validar clave primaria (primary_key)
        primary_key = schema.get("primary_key", [])
        if primary_key:
            pk_cols = [c for c in primary_key if c in df_cols]
            if pk_cols:
                if df.select(pk_cols).null_count().sum_horizontal().sum() > 0:
                    errors.append(f"Clave primaria {primary_key} contiene valores nulos")
                pk_df = df.select(pk_cols)
                if pk_df.height != pk_df.unique().height:
                    errors.append(f"Clave primaria {primary_key} tiene valores duplicados")

        # 4. Verificar expected_record_count (solo advertencia)
        expected = schema.get("expected_record_count")
        if expected is not None and df.height != expected:
            warnings.append(
                f"Cantidad de registros ({df.height}) difiere de la esperada ({expected})"
            )

        status = "ok" if not errors else "error"
        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "schema_used": str(schema_path),
        }

    def search_datasets(
        self, query: str = "", source_name: str = "", maturity: str = ""
    ) -> list[dict]:
        """Busca datasets por keyword, fuente, o nivel de madurez.

        Args:
            query: Texto libre para buscar en nombre y descripción.
            source_name: Filtrar por fuente (ej. "INE", "MINSAL"). Coincidencia parcial
                sin distinción de mayúsculas.
            maturity: Filtrar por maturity_status (ej. "stable", "candidate").

        Returns:
            Lista de dicts con información de cada dataset que coincide:
            {"name", "description", "source_name", "record_count", "maturity_status", "fields"}.
        """
        results = []
        query_lower = query.lower().strip() if query else ""
        source_lower = source_name.lower().strip() if source_name else ""
        maturity_lower = maturity.lower().strip() if maturity else ""

        # Cargar source_readiness para maturity_status
        source_readiness = self._load_source_readiness()
        maturity_by_dataset = {
            entry["dataset"]: entry.get("maturity_status", "")
            for entry in source_readiness.get("datasets", [])
        }

        for entry in self.catalog.get("datasets", []):
            name = entry.get("dataset", "")
            desc = entry.get("description", "").lower()

            # Filtro por query
            if query_lower:
                if query_lower not in name.lower() and query_lower not in desc:
                    continue

            # Filtro por fuente
            entry_source = entry.get("source_name", "").lower()
            if source_lower and source_lower not in entry_source:
                continue

            # Filtro por maturity_status
            if maturity_lower:
                entry_maturity = maturity_by_dataset.get(name, "").lower()
                if maturity_lower != entry_maturity:
                    continue

            results.append(
                {
                    "name": name,
                    "description": entry.get("description", ""),
                    "source_name": entry.get("source_name", ""),
                    "record_count": entry.get("record_count", 0),
                    "maturity_status": maturity_by_dataset.get(name, ""),
                    "fields": entry.get("fields", []),
                }
            )

        return results

    def example_usage(self, dataset_name: str | Dataset, kind: str = "python") -> str:
        dataset_name = _resolve_dataset_name(dataset_name)
        dataset = self.get_dataset(dataset_name)
        examples = dataset.get("usage_examples", {})
        if kind not in examples:
            available_examples = sorted(examples.keys())
            raise ChileHubExampleError(
                f"Example '{kind}' no existe para '{dataset_name}'. "
                f"{_format_available(available_examples, kind)}"
            )
        return examples[kind]  # type: ignore[no-any-return]  # str en runtime

    def summary(self) -> list[dict[str, Any]]:
        return [
            {
                "dataset": entry["dataset"],
                "source_mode": entry["source_mode"],
                "record_count": entry["record_count"],
                "join_keys": entry.get("join_keys", []),
                "confidence_tier": entry.get("confidence_tier"),
                "reuse_status": entry.get("reuse_policy", {}).get("status"),
                "reuse_license": entry.get("reuse_policy", {}).get("license"),
                "attribution_required": entry.get("reuse_policy", {}).get("attribution_required"),
                "freshness_status": entry.get("freshness", {}).get("status"),
                "freshness_age_hours": entry.get("freshness", {}).get("age_hours"),
                "coverage_status": entry.get("coverage", {}).get("status"),
                "coverage_ratio": entry.get("coverage", {}).get("coverage_ratio"),
                "validation_status": entry.get("validation_status"),
                "warning_count": len(entry.get("warnings", [])),
                "drift_status": entry.get("drift", {}).get("status"),
                "drift_summary": entry.get("drift", {}).get("summary"),
                "degradation_status": entry.get("degradation", {}).get("status"),
                "degradation_impact": entry.get("degradation", {}).get("impact"),
            }
            for entry in self.catalog.get("datasets", [])
        ]

    def summary_table(self) -> str:
        rows = self.summary()
        table_rows = [
            [
                entry.get("dataset", "unknown"),
                entry.get("source_mode", "unknown"),
                str(entry.get("record_count", "N/D")),
                entry.get("freshness_status", "unknown"),
                entry.get("coverage_status", "unknown"),
                entry.get("validation_status", "unknown"),
                entry.get("drift_status", "unknown"),
                str(entry.get("warning_count", 0)),
            ]
            for entry in rows
        ]
        return render_table(
            "chile-hub summary",
            [
                "dataset",
                "mode",
                "records",
                "freshness",
                "coverage",
                "validation",
                "drift",
                "warnings",
            ],
            table_rows,
        )

    def snapshot_text(self):
        overview = self.overview()
        freshness_audit = self.freshness_audit()
        runtime_status = self.runtime_status_audit()
        freshness_by_dataset = {
            entry.get("dataset"): entry for entry in freshness_audit.get("datasets", [])
        }
        package = overview.get("primary_package") or {}
        top_issue = overview.get("top_issue")
        lines = [
            "chile-hub snapshot",
            f"generated_at_utc: {overview.get('generated_at_utc', 'unknown')}",
            (
                f"status_build: {overview.get('build_overall_status', overview.get('overall_status', 'unknown'))} | "
                f"status_current: {overview.get('current_overall_status', runtime_status.get('current_overall_status', 'unknown'))} | "
                f"datasets={overview.get('dataset_count', 0)} | "
                f"live={overview.get('live_count', 0)} | "
                f"stale={overview.get('stale_count', 0)} | "
                f"drifted={overview.get('drifted_count', 0)} | "
                f"warnings={overview.get('warning_count', 0)}"
            ),
            (
                f"current_freshness: fresh={freshness_audit.get('fresh_count', 0)} | "
                f"stale={freshness_audit.get('stale_count', 0)} | "
                f"unknown={freshness_audit.get('unknown_count', 0)} | "
                f"checked_at={freshness_audit.get('checked_at_utc', 'unknown')}"
            ),
        ]
        if top_issue:
            lines.append(
                f"top_issue: {top_issue.get('dataset')} | "
                f"build={top_issue.get('build_freshness_status', 'unknown')} | "
                f"current={top_issue.get('current_freshness_status', 'unknown')} | "
                f"drift={top_issue.get('drift_status', 'unknown')} | "
                f"warnings={top_issue.get('warning_count', 0)}"
            )
            lines.append(f"top_issue_reason: {top_issue.get('diagnostic_summary', 'unknown')}")
            lines.append(f"top_issue_action: {top_issue.get('recommended_action', 'unknown')}")

        if package:
            lines.append(
                f"package: {package.get('path', 'unknown')} | "
                f"{package.get('package_type', 'unknown')} | "
                f"checksum={package.get('checksum_algorithm', 'unknown')}"
            )
            lines.append(f"verify: {package.get('verification_command', 'unknown')}")

        lines.append("")
        for entry in overview.get("datasets", []):
            runtime_freshness = freshness_by_dataset.get(entry.get("dataset"), {})
            lines.append(
                f"- {entry.get('dataset', 'unknown')}: "
                f"mode={entry.get('source_mode', 'unknown')}, "
                f"validation={entry.get('validation_status', 'unknown')}, "
                f"freshness_build={entry.get('freshness_status', 'unknown')}, "
                f"freshness_now={runtime_freshness.get('current_freshness_status', 'unknown')}, "
                f"coverage={entry.get('coverage_status', 'unknown')}, "
                f"drift={entry.get('drift_status', 'unknown')}"
            )

        return "\n".join(lines) + "\n"

    def snapshot_table(self):
        overview = self.overview()
        freshness_audit = self.freshness_audit()
        freshness_by_dataset = {
            entry.get("dataset"): entry for entry in freshness_audit.get("datasets", [])
        }
        rows = [
            ("generated_at_utc", overview.get("generated_at_utc", "unknown")),
            (
                "build_overall_status",
                overview.get("build_overall_status", overview.get("overall_status", "unknown")),
            ),
            (
                "current_overall_status",
                overview.get("current_overall_status", "unknown"),
            ),
            ("datasets", str(overview.get("dataset_count", 0))),
            ("live", str(overview.get("live_count", 0))),
            ("stale", str(overview.get("stale_count", 0))),
            ("drifted", str(overview.get("drifted_count", 0))),
            ("warnings", str(overview.get("warning_count", 0))),
            ("current_fresh", str(freshness_audit.get("fresh_count", 0))),
            ("current_stale", str(freshness_audit.get("stale_count", 0))),
            ("current_unknown", str(freshness_audit.get("unknown_count", 0))),
            ("audit_checked", freshness_audit.get("checked_at_utc", "unknown")),
        ]
        top_issue = overview.get("top_issue")
        if top_issue:
            rows.extend(
                [
                    ("top_issue", top_issue.get("dataset", "unknown")),
                    (
                        "top_issue_build",
                        top_issue.get("build_freshness_status", "unknown"),
                    ),
                    (
                        "top_issue_current",
                        top_issue.get("current_freshness_status", "unknown"),
                    ),
                    ("top_issue_drift", top_issue.get("drift_status", "unknown")),
                    (
                        "top_issue_reason",
                        top_issue.get("diagnostic_summary", "unknown"),
                    ),
                    (
                        "top_issue_action",
                        top_issue.get("recommended_action", "unknown"),
                    ),
                    (
                        "top_issue_summary",
                        overview.get("top_issue_summary", format_top_issue_summary(top_issue)),
                    ),
                ]
            )

        package = overview.get("primary_package") or {}
        if package:
            rows.extend(
                [
                    ("package_path", package.get("path", "unknown")),
                    ("package_type", package.get("package_type", "unknown")),
                    ("checksum", package.get("checksum_algorithm", "unknown")),
                    ("verify", package.get("verification_command", "unknown")),
                ]
            )

        label_width = max(len(label) for label, _ in rows)
        lines = ["chile-hub snapshot table", ""]
        lines.extend(f"{label.ljust(label_width)} : {value}" for label, value in rows)

        dataset_rows = []
        for entry in overview.get("datasets", []):
            runtime_freshness = freshness_by_dataset.get(entry.get("dataset"), {})
            dataset_rows.append(
                [
                    entry.get("dataset", "unknown"),
                    entry.get("source_mode", "unknown"),
                    entry.get("validation_status", "unknown"),
                    entry.get("freshness_status", "unknown"),
                    runtime_freshness.get("current_freshness_status", "unknown"),
                    entry.get("coverage_status", "unknown"),
                    entry.get("drift_status", "unknown"),
                ]
            )

        lines.append("")
        lines.append(
            render_table(
                "",
                ["dataset", "mode", "validation", "build", "current", "coverage", "drift"],
                dataset_rows,
            )
        )
        return "\n".join(lines) + "\n"

    def artifacts(self, dataset_name=None):
        manifest = self._load_artifact_manifest()
        artifacts = manifest.get("artifacts", [])
        if dataset_name is None:
            return artifacts

        self.get_dataset(dataset_name)
        return [entry for entry in artifacts if entry.get("dataset") == dataset_name]

    def shared_artifacts(self, shared_type=None, format=None):
        artifacts = [entry for entry in self.artifacts() if entry.get("shared_type")]
        if shared_type is not None:
            artifacts = [entry for entry in artifacts if entry.get("shared_type") == shared_type]
        if format is not None:
            artifacts = [entry for entry in artifacts if entry.get("format") == format]
        return artifacts

    def shared_artifacts_table(self, shared_type=None, format=None):
        artifacts = self.shared_artifacts(shared_type, format)
        table_rows = []
        for entry in artifacts:
            size_bytes = entry.get("size_bytes")
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    size_label = f"{size_bytes} B"
                else:
                    size_label = f"{size_bytes / 1024:.1f} KB"
            else:
                size_label = "N/D"
            table_rows.append(
                [
                    entry.get("shared_type", "unknown"),
                    entry.get("format", "unknown"),
                    size_label,
                    entry.get("path", "unknown"),
                ]
            )
        return render_table(
            "chile-hub shared artifacts",
            ["shared_type", "format", "size", "path"],
            table_rows,
        )

    def reports(self):
        return self.bundle().get("reports", {})

    def report_index(self):
        rows = []
        for report_key, entry in sorted(self.reports().items()):
            rows.append(
                {
                    "report_key": report_key,
                    "shared_type": entry.get("shared_type"),
                    "format": entry.get("format"),
                    "path": entry.get("path"),
                    "size_bytes": entry.get("size_bytes"),
                    "sha256": entry.get("sha256"),
                }
            )
        return rows

    def report_index_table(self):
        rows = self.report_index()
        table_rows = []
        for entry in rows:
            size_bytes = entry.get("size_bytes")
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    size_label = f"{size_bytes} B"
                else:
                    size_label = f"{size_bytes / 1024:.1f} KB"
            else:
                size_label = "N/D"
            table_rows.append(
                [
                    entry.get("report_key", "unknown"),
                    entry.get("shared_type", "unknown"),
                    entry.get("format", "unknown"),
                    size_label,
                    entry.get("path", "unknown"),
                ]
            )
        return render_table(
            "chile-hub report index",
            ["report_key", "shared_type", "format", "size", "path"],
            table_rows,
        )

    def get_report(self, shared_type, format):
        for entry in self.reports().values():
            if entry.get("shared_type") == shared_type and entry.get("format") == format:
                return entry
        raise KeyError(f"Reporte '{shared_type}' con formato '{format}' no existe en el bundle.")

    def overview(self):
        health = self.health()
        bundle = self.bundle()
        packages = self.packages()
        runtime_status = self.runtime_status_audit()
        primary_package = None
        try:
            primary_package = self.primary_package()
        except KeyError:
            primary_package = None
        top_issue = self.top_issue()
        shared_artifacts = self.shared_artifacts()
        return {
            "generated_at_utc": health.get("generated_at_utc"),
            "overall_status": health.get("overall_status"),
            "build_overall_status": health.get("overall_status"),
            "current_overall_status": runtime_status.get("current_overall_status"),
            "dataset_count": health.get("dataset_count"),
            "live_count": health.get("live_count"),
            "fallback_count": health.get("fallback_count"),
            "stale_count": health.get("stale_count"),
            "drifted_count": health.get("drifted_count"),
            "degraded_count": health.get("degraded_count"),
            "partial_coverage_count": health.get("partial_coverage_count"),
            "warning_count": health.get("warning_count"),
            "current_fresh_count": runtime_status.get("fresh_count"),
            "current_stale_count": runtime_status.get("stale_count"),
            "current_unknown_count": runtime_status.get("unknown_count"),
            "current_checked_at_utc": runtime_status.get("checked_at_utc"),
            "top_issue": top_issue,
            "top_issue_summary": format_top_issue_summary(top_issue),
            "shared_artifact_count": len(shared_artifacts),
            "package_count": len(packages),
            "primary_package": (
                {
                    "path": primary_package.get("path"),
                    "package_type": primary_package.get("package_type"),
                    "size_bytes": primary_package.get("size_bytes"),
                    "checksum_algorithm": primary_package.get("checksum_algorithm"),
                    "checksum_path": primary_package.get("checksum_path"),
                    "verification_command": primary_package.get("verification_command"),
                }
                if primary_package
                else None
            ),
            "report_keys": sorted(bundle.get("reports", {}).keys()),
            "datasets": [
                {
                    "dataset": entry.get("dataset"),
                    "source_mode": entry.get("source_mode"),
                    "validation_status": entry.get("validation_status"),
                    "freshness_status": entry.get("freshness_status"),
                    "coverage_status": entry.get("coverage_status"),
                    "drift_status": entry.get("drift_status"),
                }
                for entry in health.get("datasets", [])
            ],
        }

    def overview_table(self):
        overview = self.overview()
        rows = [
            ("generated_at_utc", overview.get("generated_at_utc", "unknown")),
            ("build_overall_status", overview.get("build_overall_status", "unknown")),
            (
                "current_overall_status",
                overview.get("current_overall_status", "unknown"),
            ),
            ("datasets", str(overview.get("dataset_count", 0))),
            ("live", str(overview.get("live_count", 0))),
            ("fallback", str(overview.get("fallback_count", 0))),
            ("build_stale", str(overview.get("stale_count", 0))),
            ("current_fresh", str(overview.get("current_fresh_count", 0))),
            ("current_stale", str(overview.get("current_stale_count", 0))),
            ("current_unknown", str(overview.get("current_unknown_count", 0))),
            ("drifted", str(overview.get("drifted_count", 0))),
            ("degraded", str(overview.get("degraded_count", 0))),
            ("partial_coverage", str(overview.get("partial_coverage_count", 0))),
            ("warnings", str(overview.get("warning_count", 0))),
            ("shared_artifacts", str(overview.get("shared_artifact_count", 0))),
            ("packages", str(overview.get("package_count", 0))),
            ("current_checked_at", overview.get("current_checked_at_utc", "unknown")),
        ]
        top_issue = overview.get("top_issue")
        if top_issue:
            rows.extend(
                [
                    ("top_issue", top_issue.get("dataset", "unknown")),
                    (
                        "top_issue_build",
                        top_issue.get("build_freshness_status", "unknown"),
                    ),
                    (
                        "top_issue_current",
                        top_issue.get("current_freshness_status", "unknown"),
                    ),
                    ("top_issue_drift", top_issue.get("drift_status", "unknown")),
                    (
                        "top_issue_reason",
                        top_issue.get("diagnostic_summary", "unknown"),
                    ),
                    (
                        "top_issue_action",
                        top_issue.get("recommended_action", "unknown"),
                    ),
                    (
                        "top_issue_summary",
                        overview.get("top_issue_summary", format_top_issue_summary(top_issue)),
                    ),
                ]
            )

        package = overview.get("primary_package") or {}
        if package:
            rows.extend(
                [
                    ("package_path", package.get("path", "unknown")),
                    ("package_type", package.get("package_type", "unknown")),
                    ("checksum", package.get("checksum_algorithm", "unknown")),
                ]
            )

        label_width = max(len(label) for label, _ in rows)
        lines = ["chile-hub overview", ""]
        lines.extend(f"{label.ljust(label_width)} : {value}" for label, value in rows)

        dataset_rows = [
            [
                entry.get("dataset", "unknown"),
                entry.get("source_mode", "unknown"),
                entry.get("validation_status", "unknown"),
                entry.get("freshness_status", "unknown"),
                entry.get("coverage_status", "unknown"),
                entry.get("drift_status", "unknown"),
            ]
            for entry in overview.get("datasets", [])
        ]

        lines.append("")
        lines.append(
            render_table(
                "",
                ["dataset", "mode", "validation", "build", "coverage", "drift"],
                dataset_rows,
            )
        )
        return "\n".join(lines) + "\n"

    def inventory(self):
        inventory = []
        manifest_artifacts = self.artifacts()
        by_dataset: dict[str, list[dict[str, Any]]] = {}
        for artifact in manifest_artifacts:
            dataset = artifact.get("dataset")
            if not dataset:
                continue
            by_dataset.setdefault(dataset, []).append(artifact)

        for entry in self.catalog.get("datasets", []):
            dataset_name = entry["dataset"]
            artifacts = sorted(
                by_dataset.get(dataset_name, []),
                key=lambda item: (
                    item.get("output_type") or "",
                    item.get("path") or "",
                ),
            )
            published_outputs = [
                artifact["output_type"] for artifact in artifacts if artifact.get("output_type")
            ]
            inventory.append(
                {
                    "dataset": dataset_name,
                    "source_mode": entry.get("source_mode"),
                    "record_count": entry.get("record_count"),
                    "validation_status": entry.get("validation_status"),
                    "confidence_tier": entry.get("confidence_tier"),
                    "reuse_status": entry.get("reuse_policy", {}).get("status"),
                    "reuse_license": entry.get("reuse_policy", {}).get("license"),
                    "attribution_required": entry.get("reuse_policy", {}).get(
                        "attribution_required"
                    ),
                    "freshness_status": entry.get("freshness", {}).get("status"),
                    "freshness_age_hours": entry.get("freshness", {}).get("age_hours"),
                    "coverage_status": entry.get("coverage", {}).get("status"),
                    "coverage_ratio": entry.get("coverage", {}).get("coverage_ratio"),
                    "warning_count": len(entry.get("warnings", [])),
                    "drift_status": entry.get("drift", {}).get("status"),
                    "drift_summary": entry.get("drift", {}).get("summary"),
                    "degradation_status": entry.get("degradation", {}).get("status"),
                    "degradation_impact": entry.get("degradation", {}).get("impact"),
                    "published_outputs": published_outputs,
                    "artifact_count": len(artifacts),
                    "total_size_bytes": sum(
                        artifact.get("size_bytes", 0) for artifact in artifacts
                    ),
                    "artifacts": [
                        {
                            "path": artifact.get("path"),
                            "output_type": artifact.get("output_type"),
                            "size_bytes": artifact.get("size_bytes"),
                        }
                        for artifact in artifacts
                    ],
                }
            )
        return inventory

    def inventory_table(self):
        rows = self.inventory()
        table_rows = []
        for entry in rows:
            outputs = ",".join(entry.get("published_outputs", [])) or "N/D"
            size_bytes = entry.get("total_size_bytes")
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    size_label = f"{size_bytes} B"
                else:
                    size_label = f"{size_bytes / 1024:.1f} KB"
            else:
                size_label = "N/D"
            table_rows.append(
                [
                    entry.get("dataset", "unknown"),
                    entry.get("source_mode", "unknown"),
                    str(entry.get("record_count", "N/D")),
                    outputs,
                    size_label,
                    entry.get("freshness_status", "unknown"),
                    entry.get("coverage_status", "unknown"),
                    entry.get("drift_status", "unknown"),
                ]
            )
        return render_table(
            "chile-hub inventory",
            ["dataset", "mode", "records", "outputs", "size", "freshness", "coverage", "drift"],
            table_rows,
        )

    def health(self):
        health = self._load_hub_health()
        if "top_issue_summary" not in health:
            health["top_issue_summary"] = format_top_issue_summary(health.get("top_issue"))
        return health

    def status(self):
        status = self._load_hub_status()
        if "top_issue_summary" not in status:
            status["top_issue_summary"] = format_top_issue_summary(status.get("top_issue"))
        return status

    def dataset_status(self):
        return self._load_dataset_status()

    def dataset_changelog(self):
        return self._load_dataset_changelog()

    def source_readiness(self):
        """Devuelve el reporte de madurez de fuente por dataset."""
        return self._load_source_readiness()

    def check_sources(self, timeout: int = 5) -> list[dict[str, Any]]:
        """Verifica la conectividad de red con las fuentes de datos oficiales."""
        results = []
        for entry in self.catalog.get("datasets", []):
            dataset = entry.get("dataset")
            url = entry.get("source_url")
            source_name = entry.get("source_name")
            if not url:
                results.append(
                    {
                        "dataset": dataset,
                        "source_name": source_name,
                        "url": "N/A",
                        "status": "offline",
                        "status_code": None,
                        "latency_ms": None,
                        "error": "No source URL defined",
                    }
                )
                continue

            try:
                # Intenta HEAD primero
                response = requests.head(url, timeout=timeout, allow_redirects=True)
                if response.status_code >= 400:
                    response.close()
                    response = requests.get(url, timeout=timeout, stream=True)

                status = "online" if response.status_code < 400 else "offline"
                status_code = response.status_code
                latency_ms = round(response.elapsed.total_seconds() * 1000, 2)
                error = None
                response.close()
            except Exception as e:
                status = "offline"
                status_code = None
                latency_ms = None
                error = type(e).__name__

            results.append(
                {
                    "dataset": dataset,
                    "source_name": source_name,
                    "url": url,
                    "status": status,
                    "status_code": status_code,
                    "latency_ms": latency_ms,
                    "error": error,
                }
            )
        return results

    def check_sources_table(self, results: list[dict[str, Any]]) -> str:
        """Formatea el resultado de check_sources como una tabla amigable para terminal."""
        table_rows = []
        for entry in results:
            status = entry.get("status", "unknown")
            code = str(entry.get("status_code")) if entry.get("status_code") is not None else "N/A"
            latency = (
                f"{entry.get('latency_ms')}ms" if entry.get("latency_ms") is not None else "N/A"
            )
            url = entry.get("url", "N/A")
            if len(url) > 48:
                url = url[:45] + "..."
            table_rows.append(
                [
                    entry.get("dataset", "unknown"),
                    status,
                    code,
                    latency,
                    entry.get("source_name", "unknown"),
                    url,
                ]
            )
        return render_table(
            "chile-hub check-sources",
            ["dataset", "status", "code", "latency", "source name", "url"],
            table_rows,
        )

    def dataset_quality(self):
        """Devuelve la tarjeta de puntuación de calidad multidimensional por dataset."""
        return self._load_dataset_quality()

    def status_table(self):
        status = self.status()
        table_rows = [
            ["generated_at_utc", status.get("generated_at_utc", "unknown")],
            ["overall_status", status.get("overall_status", "unknown")],
            ["dataset_count", str(status.get("dataset_count", 0))],
            ["live_count", str(status.get("live_count", 0))],
            ["fallback_count", str(status.get("fallback_count", 0))],
            ["stale_count", str(status.get("stale_count", 0))],
            ["drifted_count", str(status.get("drifted_count", 0))],
            ["degraded_count", str(status.get("degraded_count", 0))],
            ["warning_count", str(status.get("warning_count", 0))],
        ]
        top_issue = status.get("top_issue")
        if top_issue:
            table_rows.extend(
                [
                    ["top_issue", top_issue.get("dataset", "unknown")],
                    ["top_issue_reason", top_issue.get("diagnostic_summary", "unknown")],
                    ["top_issue_action", top_issue.get("recommended_action", "unknown")],
                    [
                        "top_issue_summary",
                        status.get("top_issue_summary", format_top_issue_summary(top_issue)),
                    ],
                ]
            )
        return render_table("chile-hub status", ["key", "value"], table_rows)

    def health_table(self):
        health = self.health()
        lines = ["chile-hub health", ""]
        lines.append(
            "overall="
            f"{health.get('overall_status', 'unknown')} | "
            f"datasets={health.get('dataset_count', 0)} | "
            f"ok={health.get('ok_count', 0)} | "
            f"warn={health.get('warn_count', 0)} | "
            f"error={health.get('error_count', 0)} | "
            f"live={health.get('live_count', 0)} | "
            f"fallback={health.get('fallback_count', 0)} | "
            f"stale={health.get('stale_count', 0)} | "
            f"drifted={health.get('drifted_count', 0)}"
        )

        dataset_rows = [
            [
                entry.get("dataset", "unknown"),
                entry.get("severity", "unknown"),
                entry.get("source_mode", "unknown"),
                entry.get("freshness_status", "unknown"),
                entry.get("validation_status", "unknown"),
                entry.get("publishability_status", "unknown"),
                entry.get("coverage_status", "unknown"),
                entry.get("drift_status", "unknown"),
                str(entry.get("warning_count", 0)),
            ]
            for entry in health.get("datasets", [])
        ]
        lines.append("")
        lines.append(
            render_table(
                "",
                [
                    "dataset",
                    "severity",
                    "mode",
                    "freshness",
                    "validation",
                    "reuse",
                    "coverage",
                    "drift",
                    "warnings",
                ],
                dataset_rows,
            )
        )
        return "\n".join(lines) + "\n"

    def freshness_audit(self):
        checked_at = datetime.now(UTC)
        datasets = []
        fresh_count = 0
        stale_count = 0
        unknown_count = 0

        for entry in self.catalog.get("datasets", []):
            max_age_hours = entry.get("freshness_policy", {}).get("max_age_hours")
            freshness = compute_freshness(entry.get("refreshed_at_utc"), max_age_hours, checked_at)
            current_status = freshness["status"]

            if current_status == "fresh":
                fresh_count += 1
            elif current_status == "stale":
                stale_count += 1
            else:
                unknown_count += 1

            datasets.append(
                {
                    "dataset": entry.get("dataset"),
                    "source_mode": entry.get("source_mode"),
                    "refreshed_at_utc": entry.get("refreshed_at_utc"),
                    "build_freshness_status": entry.get("freshness", {}).get("status"),
                    "current_freshness_status": current_status,
                    "current_age_hours": freshness["age_hours"],
                    "max_age_hours": freshness["max_age_hours"],
                    "freshness_label": entry.get("freshness_policy", {}).get("label"),
                }
            )

        return {
            "checked_at_utc": checked_at.isoformat(),
            "dataset_count": len(datasets),
            "fresh_count": fresh_count,
            "stale_count": stale_count,
            "unknown_count": unknown_count,
            "datasets": datasets,
        }

    def runtime_status_audit(self):
        health = self.health()
        freshness_audit = self.freshness_audit()
        build_overall_status = health.get("overall_status", "unknown")
        runtime_freshness_status = "ok"
        if freshness_audit.get("unknown_count", 0) > 0 or freshness_audit.get("stale_count", 0) > 0:
            runtime_freshness_status = "warn"
        current_overall_status = self._max_status(build_overall_status, runtime_freshness_status)
        return {
            "build_overall_status": build_overall_status,
            "current_overall_status": current_overall_status,
            "fresh_count": freshness_audit.get("fresh_count", 0),
            "stale_count": freshness_audit.get("stale_count", 0),
            "unknown_count": freshness_audit.get("unknown_count", 0),
            "checked_at_utc": freshness_audit.get("checked_at_utc"),
        }

    def runtime_status(self):
        health = self.health()
        runtime_audit = self.runtime_status_audit()
        freshness_by_dataset = {
            entry.get("dataset"): entry for entry in self.freshness_audit().get("datasets", [])
        }
        datasets = []
        for entry in health.get("datasets", []):
            freshness_entry = freshness_by_dataset.get(entry.get("dataset"), {})
            datasets.append(
                {
                    "dataset": entry.get("dataset"),
                    "source_mode": entry.get("source_mode"),
                    "severity": entry.get("severity"),
                    "validation_status": entry.get("validation_status"),
                    "build_freshness_status": entry.get("freshness_status"),
                    "current_freshness_status": freshness_entry.get(
                        "current_freshness_status", "unknown"
                    ),
                    "current_age_hours": freshness_entry.get("current_age_hours"),
                    "max_age_hours": freshness_entry.get("max_age_hours"),
                    "coverage_status": entry.get("coverage_status"),
                    "drift_status": entry.get("drift_status"),
                    "warning_count": entry.get("warning_count", 0),
                }
            )
        top_issue = self.top_issue()
        return {
            "generated_at_utc": health.get("generated_at_utc"),
            "build_overall_status": runtime_audit.get("build_overall_status"),
            "current_overall_status": runtime_audit.get("current_overall_status"),
            "dataset_count": health.get("dataset_count"),
            "live_count": health.get("live_count"),
            "fallback_count": health.get("fallback_count"),
            "fresh_count": runtime_audit.get("fresh_count"),
            "stale_count": runtime_audit.get("stale_count"),
            "unknown_count": runtime_audit.get("unknown_count"),
            "drifted_count": health.get("drifted_count"),
            "warning_count": health.get("warning_count"),
            "checked_at_utc": runtime_audit.get("checked_at_utc"),
            "top_issue": top_issue,
            "top_issue_summary": format_top_issue_summary(top_issue),
            "datasets": datasets,
        }

    def runtime_status_table(self):
        runtime = self.runtime_status()
        lines = ["chile-hub runtime status", ""]
        lines.append(
            f"build={runtime.get('build_overall_status', 'unknown')} | "
            f"current={runtime.get('current_overall_status', 'unknown')} | "
            f"datasets={runtime.get('dataset_count', 0)} | "
            f"live={runtime.get('live_count', 0)} | "
            f"fresh={runtime.get('fresh_count', 0)} | "
            f"stale={runtime.get('stale_count', 0)} | "
            f"unknown={runtime.get('unknown_count', 0)} | "
            f"drifted={runtime.get('drifted_count', 0)} | "
            f"warnings={runtime.get('warning_count', 0)} | "
            f"checked_at={runtime.get('checked_at_utc', 'unknown')}"
        )
        if runtime.get("top_issue"):
            top_issue = runtime["top_issue"]
            lines.append(
                f"top_issue={top_issue.get('dataset', 'unknown')} | "
                f"build={top_issue.get('build_freshness_status', 'unknown')} | "
                f"current={top_issue.get('current_freshness_status', 'unknown')} | "
                f"drift={top_issue.get('drift_status', 'unknown')} | "
                f"warnings={top_issue.get('warning_count', 0)}"
            )
            lines.append(f"top_issue_reason={top_issue.get('diagnostic_summary', 'unknown')}")
            lines.append(f"top_issue_action={top_issue.get('recommended_action', 'unknown')}")
            lines.append(
                f"top_issue_summary={runtime.get('top_issue_summary', format_top_issue_summary(top_issue))}"
            )

        dataset_rows = []
        for entry in runtime.get("datasets", []):
            age = entry.get("current_age_hours")
            age_label = f"{age:.2f}" if isinstance(age, (int, float)) else "N/D"
            max_age = entry.get("max_age_hours")
            max_age_label = str(max_age) if isinstance(max_age, (int, float)) else "N/D"
            dataset_rows.append(
                [
                    entry.get("dataset", "unknown"),
                    entry.get("source_mode", "unknown"),
                    entry.get("severity", "unknown"),
                    entry.get("build_freshness_status", "unknown"),
                    entry.get("current_freshness_status", "unknown"),
                    age_label,
                    max_age_label,
                    entry.get("coverage_status", "unknown"),
                    entry.get("drift_status", "unknown"),
                    str(entry.get("warning_count", 0)),
                ]
            )
        lines.append("")
        lines.append(
            render_table(
                "",
                [
                    "dataset",
                    "mode",
                    "severity",
                    "build",
                    "current",
                    "age_h",
                    "max_h",
                    "coverage",
                    "drift",
                    "warnings",
                ],
                dataset_rows,
            )
        )
        return "\n".join(lines) + "\n"

    def freshness_audit_table(self):
        audit = self.freshness_audit()
        lines = ["chile-hub freshness audit", ""]
        lines.append(
            f"checked_at_utc={audit.get('checked_at_utc')} | "
            f"datasets={audit.get('dataset_count', 0)} | "
            f"fresh={audit.get('fresh_count', 0)} | "
            f"stale={audit.get('stale_count', 0)} | "
            f"unknown={audit.get('unknown_count', 0)}"
        )

        dataset_rows = []
        for entry in audit.get("datasets", []):
            age = entry.get("current_age_hours")
            age_label = f"{age:.2f}" if isinstance(age, (int, float)) else "N/D"
            max_age = entry.get("max_age_hours")
            max_age_label = str(max_age) if isinstance(max_age, (int, float)) else "N/D"
            dataset_rows.append(
                [
                    entry.get("dataset", "unknown"),
                    entry.get("source_mode", "unknown"),
                    entry.get("build_freshness_status", "unknown"),
                    entry.get("current_freshness_status", "unknown"),
                    age_label,
                    max_age_label,
                    entry.get("freshness_label", "N/D"),
                ]
            )
        lines.append("")
        lines.append(
            render_table(
                "",
                ["dataset", "mode", "build", "current", "age_h", "max_h", "label"],
                dataset_rows,
            )
        )
        return "\n".join(lines) + "\n"

    def bundle(self):
        return self._load_hub_bundle()

    def packages(self):
        bundle_packages = self.bundle().get("packages", [])
        if bundle_packages:
            return bundle_packages
        manifest = self._load_artifact_manifest()
        return manifest.get("packages", [])

    def packages_table(self):
        packages = self.packages()
        table_rows = []
        for package in packages:
            size_bytes = package.get("size_bytes")
            if isinstance(size_bytes, int):
                if size_bytes < 1024:
                    size_label = f"{size_bytes} B"
                else:
                    size_label = f"{size_bytes / 1024:.1f} KB"
            else:
                size_label = "N/D"
            table_rows.append(
                [
                    package.get("package_type", "unknown"),
                    size_label,
                    package.get("checksum_algorithm", "unknown"),
                    package.get("path", "unknown"),
                ]
            )
        return render_table(
            "chile-hub packages",
            ["package_type", "size", "checksum", "path"],
            table_rows,
        )

    def primary_package(self, package_type="zip"):
        for package in self.packages():
            if package.get("package_type") == package_type:
                return package
        raise KeyError(f"No existe package_type '{package_type}' en el hub.")

    def package_verification(self, package_type="zip"):
        package = self.primary_package(package_type)
        return {
            "path": package.get("path"),
            "package_type": package.get("package_type"),
            "checksum_algorithm": package.get("checksum_algorithm"),
            "checksum_path": package.get("checksum_path"),
            "verification_command": package.get("verification_command"),
            "sha256": package.get("sha256"),
            "size_bytes": package.get("size_bytes"),
        }

    def redistribution(self):
        return self._load_redistribution_report()

    def redistribution_table(self):
        report = self.redistribution()
        lines = ["chile-hub redistribution", ""]
        lines.append(
            f"ready={report.get('ready_count', 0)} | "
            f"review_terms={report.get('review_terms_count', 0)} | "
            f"unknown={report.get('unknown_count', 0)} | "
            f"datasets={report.get('dataset_count', 0)}"
        )

        dataset_rows = []
        for entry in report.get("datasets", []):
            attribution = "yes" if entry.get("attribution_required") else "no"
            dataset_rows.append(
                [
                    entry.get("dataset", "unknown"),
                    entry.get("publishability_status", "unknown"),
                    entry.get("reuse_status", "unknown"),
                    attribution,
                    entry.get("license", "unknown"),
                ]
            )
        lines.append("")
        lines.append(
            render_table(
                "",
                ["dataset", "status", "reuse_status", "attribution", "license"],
                dataset_rows,
            )
        )
        return "\n".join(lines) + "\n"

    def provenance(self):
        return self._load_provenance_report()

    def provenance_table(self):
        report = self.provenance()
        lines = ["chile-hub provenance", ""]
        lines.append(
            f"datasets={report.get('dataset_count', 0)} | "
            f"live={report.get('live_count', 0)} | "
            f"fallback={report.get('fallback_count', 0)}"
        )

        dataset_rows = [
            [
                entry.get("dataset", "unknown"),
                entry.get("source_mode", "unknown"),
                entry.get("source_detail", "unknown"),
                entry.get("freshness_status", "unknown"),
                str(entry.get("warning_count", 0)),
                entry.get("refreshed_at_utc", "unknown"),
            ]
            for entry in report.get("datasets", [])
        ]
        lines.append("")
        lines.append(
            render_table(
                "",
                ["dataset", "mode", "source", "freshness", "warnings", "refreshed_at_utc"],
                dataset_rows,
            )
        )
        return "\n".join(lines) + "\n"

    def drift(self):
        return self._load_drift_report()

    def drift_table(self):
        report = self.drift()
        lines = ["chile-hub drift", ""]
        lines.append(
            f"datasets={report.get('dataset_count', 0)} | "
            f"drifted={report.get('drifted_count', 0)} | "
            f"healthy={report.get('healthy_count', 0)} | "
            f"fallback={report.get('fallback_count', 0)} | "
            f"partial_coverage={report.get('partial_coverage_count', 0)} | "
            f"degraded={report.get('degraded_count', 0)}"
        )

        dataset_rows = [
            [
                entry.get("dataset", "unknown"),
                entry.get("drift_status", "unknown"),
                entry.get("source_mode", "unknown"),
                entry.get("coverage_status", "unknown"),
                entry.get("degradation_status", "unknown"),
                str(entry.get("warning_count", 0)),
            ]
            for entry in report.get("datasets", [])
        ]
        lines.append("")
        lines.append(
            render_table(
                "",
                ["dataset", "drift", "mode", "coverage", "degradation", "warnings"],
                dataset_rows,
            )
        )
        return "\n".join(lines) + "\n"


def build_parser():  # pragma: no cover — entry point de CLI, testeado vía integración
    parser = argparse.ArgumentParser(description="CLI minima para inspeccionar chile-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Mostrar version instalada de chile-hub")

    cache_parser = subparsers.add_parser("cache", help="Administrar cache local de datos")
    cache_subparsers = cache_parser.add_subparsers(dest="cache_command", required=True)
    cache_subparsers.add_parser("status", help="Mostrar estado del cache local")
    cache_update_parser = cache_subparsers.add_parser(
        "update", help="Descargar o actualizar artefactos normalizados"
    )
    cache_update_parser.add_argument(
        "--data-version",
        default="latest",
        help="Version de datos o tag de GitHub Release a descargar",
    )
    cache_subparsers.add_parser("clear", help="Eliminar cache local de chile-hub")

    subparsers.add_parser("list", help="Listar datasets disponibles")

    show_parser = subparsers.add_parser("show", help="Mostrar metadata de un dataset")
    show_parser.add_argument("dataset", help="Nombre del dataset")

    path_parser = subparsers.add_parser("path", help="Resolver path de salida de un dataset")
    path_parser.add_argument("dataset", help="Nombre del dataset")
    path_parser.add_argument(
        "--output",
        default="parquet",
        help="Tipo de output a resolver, por ejemplo parquet, json o sqlite_table",
    )

    example_parser = subparsers.add_parser("example", help="Mostrar ejemplo de uso de un dataset")
    example_parser.add_argument("dataset", help="Nombre del dataset")
    example_parser.add_argument(
        "--kind",
        default="python",
        help="Tipo de ejemplo a mostrar, por ejemplo python, duckdb o cli",
    )

    artifacts_parser = subparsers.add_parser("artifacts", help="Mostrar artefactos publicables")
    artifacts_parser.add_argument(
        "dataset",
        nargs="?",
        help="Nombre opcional de dataset para filtrar artefactos",
    )

    shared_artifacts_parser = subparsers.add_parser(
        "shared-artifacts", help="Mostrar artefactos compartidos del hub"
    )
    shared_artifacts_parser.add_argument("--shared-type", help="Filtrar por shared_type")
    shared_artifacts_parser.add_argument(
        "--artifact-format",
        help="Filtrar por formato de artifact, por ejemplo json o markdown",
    )
    shared_artifacts_parser.add_argument(
        "--output",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de shared-artifacts",
    )

    reports_parser = subparsers.add_parser("reports", help="Listar reportes compartidos del hub")
    reports_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del indice de reportes",
    )

    report_parser = subparsers.add_parser(
        "report", help="Resolver metadata de un reporte compartido"
    )
    report_parser.add_argument(
        "shared_type", help="shared_type del reporte, por ejemplo hub_health"
    )
    report_parser.add_argument(
        "--format",
        default="json",
        help="Formato del reporte, por ejemplo json o markdown",
    )

    inventory_parser = subparsers.add_parser(
        "inventory", help="Mostrar inventario compacto de datasets y artefactos"
    )
    inventory_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del inventario",
    )
    snapshot_parser = subparsers.add_parser(
        "snapshot", help="Mostrar snapshot humano y compacto del hub"
    )
    snapshot_parser.add_argument(
        "--format",
        choices=["text", "table"],
        default="text",
        help="Formato de salida del snapshot",
    )
    overview_parser = subparsers.add_parser(
        "overview", help="Mostrar vista agregada compacta del hub"
    )
    overview_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de overview",
    )
    status_parser = subparsers.add_parser(
        "status", help="Mostrar status operativo compacto del hub"
    )
    status_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de status",
    )
    status_parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Retorna exit code 1 si overall_status no es 'ok'.",
    )
    subparsers.add_parser("dataset-status", help="Mostrar status detallado por dataset")
    subparsers.add_parser("dataset-changelog", help="Mostrar changelog de datasets")
    subparsers.add_parser("source-readiness", help="Mostrar madurez de fuente por dataset")
    subparsers.add_parser("dataset-quality", help="Mostrar puntuacion de calidad por dataset")
    health_parser = subparsers.add_parser("health", help="Mostrar salud agregada del hub")
    health_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de health",
    )
    health_parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Retorna exit code 1 si overall_status no es 'ok'.",
    )
    subparsers.add_parser("bundle", help="Mostrar bundle consolidado del hub")
    freshness_audit_parser = subparsers.add_parser(
        "freshness-audit",
        help="Recalcular frescura contra el reloj actual sin reconstruir el hub",
    )
    freshness_audit_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de freshness-audit",
    )
    runtime_status_parser = subparsers.add_parser(
        "runtime-status",
        help="Combinar estado build y estado actual recalculado del hub",
    )
    runtime_status_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de runtime-status",
    )
    top_issue_parser = subparsers.add_parser(
        "top-issue",
        help="Mostrar la capa prioritaria que requiere atención operativa",
    )
    top_issue_parser.add_argument(
        "--format",
        choices=["json", "text", "table"],
        default="json",
        help="Formato de salida de top-issue",
    )
    packages_parser = subparsers.add_parser("packages", help="Mostrar paquetes publicables del hub")
    packages_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de packages",
    )
    package_parser = subparsers.add_parser("package", help="Mostrar package principal del hub")
    package_parser.add_argument(
        "--type", default="zip", help="package_type a resolver, por ejemplo zip"
    )
    verify_package_parser = subparsers.add_parser(
        "verify-package",
        help="Mostrar metadata de verificación del package principal",
    )
    verify_package_parser.add_argument(
        "--type", default="zip", help="package_type a resolver, por ejemplo zip"
    )
    redistribution_parser = subparsers.add_parser(
        "redistribution", help="Mostrar inventario de redistribucion del hub"
    )
    redistribution_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de redistribution",
    )
    provenance_parser = subparsers.add_parser(
        "provenance", help="Mostrar inventario de procedencia del hub"
    )
    provenance_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de provenance",
    )
    drift_parser = subparsers.add_parser(
        "drift", help="Mostrar inventario de drift operativo del hub"
    )
    drift_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida de drift",
    )

    summary_parser = subparsers.add_parser("summary", help="Mostrar resumen breve de datasets")
    summary_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida del summary",
    )

    export_parser = subparsers.add_parser(
        "export", help="Exportar un dataset a un archivo (CSV, JSON o Parquet)"
    )
    export_parser.add_argument("dataset", help="Nombre del dataset a exportar")
    export_parser.add_argument(
        "--format",
        choices=["csv", "json", "parquet"],
        required=True,
        help="Formato del archivo de salida",
    )
    export_parser.add_argument(
        "--output",
        required=True,
        help="Ruta de destino del archivo exportado",
    )

    check_sources_parser = subparsers.add_parser(
        "check-sources",
        help="Verificar el estado de conexión de las fuentes externas oficiales",
    )
    check_sources_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Formato de salida de check-sources",
    )
    check_sources_parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout en segundos para la conexión HTTP",
    )
    check_sources_parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Retorna exit code 1 si alguna fuente está offline.",
    )

    # Subcomando: cross
    cross_parser = subparsers.add_parser("cross", help="Cruza datasets por clave territorial comun")
    cross_parser.add_argument("datasets", nargs="+", help="Datasets a cruzar (min 2)")
    cross_parser.add_argument(
        "--on", default="codigo_comuna", help="Clave de join (default: codigo_comuna)"
    )
    cross_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="table",
        help="Formato de salida (default: table)",
    )
    cross_parser.add_argument(
        "--output", default=None, help="Archivo de salida (.csv, .parquet, o .json)"
    )

    # Subcomando: search
    search_parser = subparsers.add_parser(
        "search", help="Busca datasets por keyword, fuente o madurez"
    )
    search_parser.add_argument(
        "query", nargs="?", default="", help="Texto de búsqueda en nombre y descripción"
    )
    search_parser.add_argument(
        "--source", default="", help="Filtrar por fuente (ej. 'INE', 'MINSAL')"
    )
    search_parser.add_argument(
        "--maturity", default="", help="Filtrar por madurez ('stable' o 'candidate')"
    )
    search_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Formato de salida (default: json)",
    )

    # Subcomando: validate
    validate_parser = subparsers.add_parser(
        "validate", help="Valida un dataset del hub o un archivo CSV/Parquet contra su schema"
    )
    validate_parser.add_argument(
        "target",
        nargs="?",
        help="Nombre del dataset del hub, o ruta a un archivo .csv/.parquet",
    )
    validate_parser.add_argument(
        "--dataset",
        help="Nombre del dataset de referencia (ej. 'comunas'). Obligatorio si se valida "
        "un archivo externo; opcional si target es un dataset del hub.",
    )

    return parser


def _main(argv=None):  # pragma: no cover — dispatch de CLI, testeado vía smoke tests
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version":
        try:
            version = importlib.metadata.version("chile-hub")
        except importlib.metadata.PackageNotFoundError:
            version = "1.0.1"
        print(version)
        return

    if args.command == "cache":
        manager = ChileHubDataManager(
            data_version=getattr(args, "data_version", "latest"),
        )
        if args.cache_command == "status":
            print(json.dumps(manager.status(), ensure_ascii=False, indent=2))
            return
        if args.cache_command == "update":
            data_dir = manager.ensure_data_dir(auto_update=True)
            print(data_dir)
            return
        if args.cache_command == "clear":
            manager.clear()
            print(manager.cache_root)
            return

    hub = ChileHub()

    if args.command == "export":
        df = hub.load_polars(args.dataset)
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "csv":
            df.write_csv(out_path)
        elif args.format == "json":
            df.write_json(out_path)
        elif args.format == "parquet":
            df.write_parquet(out_path)
        print(
            f"Dataset '{args.dataset}' exportado exitosamente a '{args.output}' ({args.format.upper()})"
        )
        return

    if args.command == "check-sources":
        timeout = getattr(args, "timeout", 5)
        results = hub.check_sources(timeout=timeout)
        if args.format == "table":
            print(hub.check_sources_table(results), end="")
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        if getattr(args, "exit_code", False):
            offline = [s for s in results if s.get("status") == "offline"]
            if offline:
                raise SystemExit(1)
        return

    if args.command == "list":
        for dataset in hub.list_datasets():
            print(dataset)
        return

    if args.command == "show":
        print(json.dumps(hub.get_dataset(args.dataset), ensure_ascii=False, indent=2))
        return

    if args.command == "path":
        print(hub.get_output_path(args.dataset, args.output))
        return

    if args.command == "example":
        print(hub.example_usage(args.dataset, args.kind))
        return

    if args.command == "artifacts":
        print(json.dumps(hub.artifacts(args.dataset), ensure_ascii=False, indent=2))
        return

    if args.command == "shared-artifacts":
        if args.output == "table":
            print(
                hub.shared_artifacts_table(args.shared_type, args.artifact_format),
                end="",
            )
        else:
            print(
                json.dumps(
                    hub.shared_artifacts(args.shared_type, args.artifact_format),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return

    if args.command == "reports":
        if args.format == "table":
            print(hub.report_index_table(), end="")
        else:
            print(json.dumps(hub.report_index(), ensure_ascii=False, indent=2))
        return

    if args.command == "report":
        print(
            json.dumps(
                hub.get_report(args.shared_type, args.format),
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "inventory":
        if args.format == "table":
            print(hub.inventory_table(), end="")
        else:
            print(json.dumps(hub.inventory(), ensure_ascii=False, indent=2))
        return

    if args.command == "snapshot":
        if args.format == "table":
            print(hub.snapshot_table(), end="")
        else:
            print(hub.snapshot_text(), end="")
        return

    if args.command == "overview":
        if args.format == "table":
            print(hub.overview_table(), end="")
        else:
            print(json.dumps(hub.overview(), ensure_ascii=False, indent=2))
        return

    if args.command == "status":
        if args.format == "table":
            print(hub.status_table(), end="")
        else:
            print(json.dumps(hub.status(), ensure_ascii=False, indent=2))
        if getattr(args, "exit_code", False):
            status_data = hub.status()
            if status_data.get("overall_status") != "ok":
                raise SystemExit(1)
        return

    if args.command == "dataset-status":
        print(json.dumps(hub.dataset_status(), ensure_ascii=False, indent=2))
        return

    if args.command == "dataset-changelog":
        print(json.dumps(hub.dataset_changelog(), ensure_ascii=False, indent=2))
        return

    if args.command == "source-readiness":
        print(json.dumps(hub.source_readiness(), ensure_ascii=False, indent=2))
        return

    if args.command == "dataset-quality":
        print(json.dumps(hub.dataset_quality(), ensure_ascii=False, indent=2))
        return

    if args.command == "health":
        if args.format == "table":
            print(hub.health_table(), end="")
        else:
            print(json.dumps(hub.health(), ensure_ascii=False, indent=2))
        if getattr(args, "exit_code", False):
            health_data = hub.health()
            if health_data.get("overall_status") != "ok":
                raise SystemExit(1)
        return

    if args.command == "bundle":
        print(json.dumps(hub.bundle(), ensure_ascii=False, indent=2))
        return

    if args.command == "freshness-audit":
        if args.format == "table":
            print(hub.freshness_audit_table(), end="")
        else:
            print(json.dumps(hub.freshness_audit(), ensure_ascii=False, indent=2))
        return

    if args.command == "runtime-status":
        if args.format == "table":
            print(hub.runtime_status_table(), end="")
        else:
            print(json.dumps(hub.runtime_status(), ensure_ascii=False, indent=2))
        return

    if args.command == "top-issue":
        top_issue = hub.top_issue()
        if args.format == "table":
            print(hub.top_issue_table(), end="")
        elif args.format == "text":
            if not top_issue:
                print("chile-hub top issue\n\nSin top issue activo.\n", end="")
            else:
                print(
                    "chile-hub top issue\n\n"
                    f"dataset={top_issue.get('dataset')} | "
                    f"build={top_issue.get('build_freshness_status', 'unknown')} | "
                    f"current={top_issue.get('current_freshness_status', 'unknown')} | "
                    f"drift={top_issue.get('drift_status', 'unknown')} | "
                    f"warnings={top_issue.get('warning_count', 0)} | "
                    f"source_detail={top_issue.get('source_detail', 'unknown')} | "
                    f"reason={top_issue.get('diagnostic_summary', 'unknown')} | "
                    f"action={top_issue.get('recommended_action', 'unknown')}\n",
                    end="",
                )
        else:
            print(json.dumps(top_issue, ensure_ascii=False, indent=2))
        return

    if args.command == "packages":
        if args.format == "table":
            print(hub.packages_table(), end="")
        else:
            print(json.dumps(hub.packages(), ensure_ascii=False, indent=2))
        return

    if args.command == "package":
        print(json.dumps(hub.primary_package(args.type), ensure_ascii=False, indent=2))
        return

    if args.command == "verify-package":
        print(json.dumps(hub.package_verification(args.type), ensure_ascii=False, indent=2))
        return

    if args.command == "redistribution":
        if args.format == "table":
            print(hub.redistribution_table(), end="")
        else:
            print(json.dumps(hub.redistribution(), ensure_ascii=False, indent=2))
        return

    if args.command == "provenance":
        if args.format == "table":
            print(hub.provenance_table(), end="")
        else:
            print(json.dumps(hub.provenance(), ensure_ascii=False, indent=2))
        return

    if args.command == "drift":
        if args.format == "table":
            print(hub.drift_table(), end="")
        else:
            print(json.dumps(hub.drift(), ensure_ascii=False, indent=2))
        return

    if args.command == "cross":
        df = hub.cross_view(args.datasets, on=args.on)
        _output_dataframe(df, args.output, args.format)
        return

    if args.command == "search":
        results = hub.search_datasets(
            query=args.query,
            source_name=args.source,
            maturity=args.maturity,
        )
        _print_result(results, args.format)
        return

    if args.command == "validate":
        if args.target is None:
            # Sin argumento: mostrar ayuda del subcomando
            parser.parse_args(["validate", "--help"])
            return

        target_path = Path(args.target)

        # Si target existe como archivo, validar archivo externo
        if target_path.exists() and target_path.suffix in (".csv", ".parquet"):
            if not args.dataset:
                raise ChileHubError("Debes especificar --dataset al validar un archivo externo.")
            if target_path.suffix == ".csv":
                df = pl.read_csv(target_path, infer_schema_length=0)
            else:
                df = pl.read_parquet(target_path)
            result = hub.validate_user_data(df, args.dataset)
        else:
            # Si no es archivo, validar dataset del hub
            dataset_name = args.dataset if args.dataset else args.target
            result = hub.validate_dataset(dataset_name)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result["status"] == "error":
            raise SystemExit(1)
        return

    if args.command == "summary":
        if args.format == "table":
            print(hub.summary_table(), end="")
        else:
            print(json.dumps(hub.summary(), ensure_ascii=False, indent=2))
        return


def main(argv=None):  # pragma: no cover — entry point de consola
    try:
        return _main(argv)
    except ChileHubError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":  # pragma: no cover
    main()
