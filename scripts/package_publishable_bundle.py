import json
import argparse
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
NORMALIZED_DIR = ROOT_DIR / "data" / "normalized"
MANIFEST_PATH = NORMALIZED_DIR / "artifact_manifest.json"
OUTPUT_ZIP_PATH = NORMALIZED_DIR / "chile-hub-publishable-bundle.zip"


def load_manifest(path=MANIFEST_PATH):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def list_artifact_paths(manifest, root_dir=ROOT_DIR):
    return [Path(root_dir) / entry["path"] for entry in manifest.get("artifacts", [])]


def list_package_paths(manifest, root_dir=ROOT_DIR):
    paths = []
    for entry in manifest.get("packages", []):
        package_path = entry.get("path")
        checksum_path = entry.get("checksum_path")
        if package_path:
            paths.append(Path(root_dir) / package_path)
        if checksum_path:
            paths.append(Path(root_dir) / checksum_path)
    return paths


def build_zip(manifest, output_path=OUTPUT_ZIP_PATH):
    artifact_paths = list_artifact_paths(manifest)
    missing = [
        str(path.relative_to(ROOT_DIR)) for path in artifact_paths if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing publishable artifacts: {', '.join(missing)}")

    output_path = Path(output_path)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in artifact_paths:
            archive.write(path, arcname=str(path.relative_to(ROOT_DIR)))
    return output_path


def clean_publishable(manifest, root_dir=ROOT_DIR):
    removed = []
    seen = set()
    manifest_path = Path(root_dir) / MANIFEST_PATH.relative_to(ROOT_DIR)
    paths = list_artifact_paths(manifest, root_dir) + list_package_paths(
        manifest, root_dir
    )
    ordered_paths = [path for path in paths if path != manifest_path] + [
        path for path in paths if path == manifest_path
    ]
    for path in ordered_paths:
        if path in seen:
            continue
        seen.add(path)
        if path.exists():
            path.unlink()
            removed.append(str(path.relative_to(root_dir)))
    return removed


def clean_publishable_from_manifest(manifest_path=MANIFEST_PATH, root_dir=ROOT_DIR):
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return []
    manifest = load_manifest(manifest_path)
    return clean_publishable(manifest, root_dir=root_dir)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Build or clean the publishable chile-hub bundle from artifact_manifest.json.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete only the publishable artifacts and packages declared in the manifest.",
    )
    return parser


def main():
    args = build_parser().parse_args()
    if args.clean:
        removed = clean_publishable_from_manifest()
        print(
            json.dumps(
                {
                    "removed_count": len(removed),
                    "removed_paths": removed,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    manifest = load_manifest()
    output_path = build_zip(manifest)
    size_bytes = output_path.stat().st_size
    print(
        json.dumps(
            {
                "zip_path": str(output_path.relative_to(ROOT_DIR)),
                "artifact_count": manifest.get("artifact_count", 0),
                "size_bytes": size_bytes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"ERROR: {exc}")
        sys.exit(1)
