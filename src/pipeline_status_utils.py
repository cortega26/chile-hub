import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
PIPELINE_METADATA_PATH = NORMALIZED_DIR / "pipeline_metadata.json"
STATUS_MARKDOWN_PATH = NORMALIZED_DIR / "pipeline_status.md"
DATASET_CATALOG_MARKDOWN_PATH = NORMALIZED_DIR / "dataset_catalog.md"


def load_metadata(path=PIPELINE_METADATA_PATH):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def format_warnings(warnings):
    if not warnings:
        return "none"
    return "; ".join(warnings)


def build_status_text(metadata):
    lines = []
    generated_at = metadata.get("generated_at_utc", "unknown")
    lines.append("chile-hub pipeline status")
    lines.append(f"generated_at_utc: {generated_at}")
    lines.append("")

    datasets = metadata.get("datasets", {})
    validations = metadata.get("validations", {})

    for dataset_name in sorted(datasets.keys()):
        dataset = datasets[dataset_name]
        validation = validations.get(dataset_name, {})

        lines.append(f"[{dataset_name}]")
        lines.append(f"source: {dataset.get('source_name', 'unknown')}")
        lines.append(f"mode: {dataset.get('source_mode', 'unknown')}")
        lines.append(f"detail: {dataset.get('source_detail', 'unknown')}")
        lines.append(f"refreshed_at_utc: {dataset.get('refreshed_at_utc', 'unknown')}")
        lines.append(f"records: {dataset.get('record_count', 'unknown')}")
        lines.append(f"validation_status: {validation.get('status', 'unknown')}")
        lines.append(f"warnings: {format_warnings(validation.get('warnings', []))}")

        notes = dataset.get("notes", [])
        if notes:
            lines.append(f"notes: {'; '.join(notes)}")

        indicator_codes = dataset.get("indicator_codes")
        if indicator_codes:
            lines.append(f"indicator_codes: {', '.join(indicator_codes)}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_status_markdown(metadata):
    generated_at = metadata.get("generated_at_utc", "unknown")
    datasets = metadata.get("datasets", {})
    validations = metadata.get("validations", {})

    lines = [
        "# chile-hub pipeline status",
        "",
        f"- `generated_at_utc`: `{generated_at}`",
        "",
        "| Dataset | Source | Mode | Detail | Records | Validation | Warnings |",
        "| :--- | :--- | :--- | :--- | ---: | :--- | :--- |",
    ]

    for dataset_name in sorted(datasets.keys()):
        dataset = datasets[dataset_name]
        validation = validations.get(dataset_name, {})
        warnings = format_warnings(validation.get("warnings", []))
        lines.append(
            "| "
            f"`{dataset_name}` | "
            f"{dataset.get('source_name', 'unknown')} | "
            f"`{dataset.get('source_mode', 'unknown')}` | "
            f"`{dataset.get('source_detail', 'unknown')}` | "
            f"{dataset.get('record_count', 'unknown')} | "
            f"`{validation.get('status', 'unknown')}` | "
            f"{warnings} |"
        )

    lines.append("")

    for dataset_name in sorted(datasets.keys()):
        dataset = datasets[dataset_name]
        validation = validations.get(dataset_name, {})
        lines.append(f"## {dataset_name}")
        lines.append("")
        lines.append(f"- `refreshed_at_utc`: `{dataset.get('refreshed_at_utc', 'unknown')}`")
        lines.append(f"- `fields`: `{', '.join(dataset.get('fields', []))}`")

        notes = dataset.get("notes", [])
        if notes:
            lines.append(f"- `notes`: {'; '.join(notes)}")

        indicator_codes = dataset.get("indicator_codes")
        if indicator_codes:
            lines.append(f"- `indicator_codes`: `{', '.join(indicator_codes)}`")

        warnings = validation.get("warnings", [])
        if warnings:
            lines.append(f"- `warnings`: {'; '.join(warnings)}")
        else:
            lines.append("- `warnings`: none")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_status_markdown_file(metadata, path=STATUS_MARKDOWN_PATH):
    Path(path).write_text(build_status_markdown(metadata), encoding="utf-8")


def build_dataset_catalog_markdown(catalog):
    lines = [
        "# chile-hub dataset catalog",
        "",
        f"- `generated_at_utc`: `{catalog.get('generated_at_utc', 'unknown')}`",
        f"- `dataset_count`: `{catalog.get('dataset_count', 0)}`",
        "",
        "| Dataset | Source | Mode | Records | Confidence | Join Keys | Validation |",
        "| :--- | :--- | :--- | ---: | :--- | :--- | :--- |",
    ]

    for entry in catalog.get("datasets", []):
        lines.append(
            "| "
            f"`{entry.get('dataset', 'unknown')}` | "
            f"{entry.get('source_name', 'unknown')} | "
            f"`{entry.get('source_mode', 'unknown')}` | "
            f"{entry.get('record_count', 'unknown')} | "
            f"`{entry.get('confidence_tier', 'unknown')}` | "
            f"`{', '.join(entry.get('join_keys', []))}` | "
            f"`{entry.get('validation_status', 'unknown')}` |"
        )

    lines.append("")

    for entry in catalog.get("datasets", []):
        lines.append(f"## {entry.get('dataset', 'unknown')}")
        lines.append("")
        lines.append(entry.get("description", ""))
        lines.append("")
        lines.append(f"- `source_url`: {entry.get('source_url', 'unknown')}")
        lines.append(f"- `documentation`: `{entry.get('documentation', 'unknown')}`")
        lines.append(f"- `fields`: `{', '.join(entry.get('fields', []))}`")
        lines.append(f"- `join_keys`: `{', '.join(entry.get('join_keys', []))}`")
        lines.append(f"- `outputs`: `{json.dumps(entry.get('outputs', {}), ensure_ascii=False)}`")
        usage_examples = entry.get("usage_examples", {})
        if usage_examples:
            lines.append(f"- `usage_examples`: `{json.dumps(usage_examples, ensure_ascii=False)}`")

        warnings = entry.get("warnings", [])
        if warnings:
            lines.append(f"- `warnings`: {'; '.join(warnings)}")
        else:
            lines.append("- `warnings`: none")

        notes = entry.get("notes", [])
        if notes:
            lines.append(f"- `notes`: {'; '.join(notes)}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_dataset_catalog_markdown_file(catalog, path=DATASET_CATALOG_MARKDOWN_PATH):
    Path(path).write_text(build_dataset_catalog_markdown(catalog), encoding="utf-8")
