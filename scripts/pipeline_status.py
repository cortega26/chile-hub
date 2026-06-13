import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.pipeline_status_utils import (
    load_metadata,
    build_status_text,
    write_status_markdown_file,
)


def main():
    metadata = load_metadata()
    print(build_status_text(metadata), end="")
    write_status_markdown_file(metadata)


if __name__ == "__main__":
    main()
