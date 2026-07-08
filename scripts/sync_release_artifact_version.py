"""Synchronize generated release artifacts with the package version.

Semantic-release bumps ``pyproject.toml`` after the pipeline artifact has already
been produced.  This script updates the version-bearing generated files so the
frontend and release assets do not advertise the previous package version.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import tomllib

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.builders.artifacts import (
    attach_publishable_package_to_manifest,
    write_artifact_manifest,
    write_publishable_bundle_sha256,
    write_publishable_bundle_zip,
)
from src.builders.io_utils import write_json_atomic
from src.builders.landing import sync_landing_metadata

NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"


def load_project_metadata() -> tuple[str, str]:
    with open(ROOT_DIR / "pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
    version = pyproject_data.get("project", {}).get("version")
    public_site_url = (
        pyproject_data.get("tool", {})
        .get("chile_hub", {})
        .get("public_site_url", "https://tooltician.com/chile-hub/")
    )
    if not version:
        raise SystemExit("pyproject.toml is missing project.version")
    return version, public_site_url


def update_json_version(path: Path, version: str) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    write_json_atomic(data, str(path), ensure_ascii=False, indent=2)
    return data


def main() -> None:
    version, public_site_url = load_project_metadata()

    required = [
        NORMALIZED_DIR / "pipeline_metadata.json",
        NORMALIZED_DIR / "hub_bundle.json",
        NORMALIZED_DIR / "datapackage.json",
    ]
    missing = [str(path.relative_to(ROOT_DIR)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"Missing generated artifacts: {', '.join(missing)}")

    update_json_version(NORMALIZED_DIR / "pipeline_metadata.json", version)
    update_json_version(NORMALIZED_DIR / "datapackage.json", version)
    hub_bundle = update_json_version(NORMALIZED_DIR / "hub_bundle.json", version)

    _, manifest = write_artifact_manifest()
    zip_path = write_publishable_bundle_zip()
    sha256_path = write_publishable_bundle_sha256(zip_path)
    _, manifest = attach_publishable_package_to_manifest(zip_path, sha256_path, manifest)

    hub_bundle["packages"] = manifest.get("packages", [])
    write_json_atomic(
        hub_bundle,
        str(NORMALIZED_DIR / "hub_bundle.json"),
        ensure_ascii=False,
        indent=2,
    )
    sync_landing_metadata(public_site_url, version)


if __name__ == "__main__":
    main()
