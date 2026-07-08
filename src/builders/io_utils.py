"""Helpers de entrada/salida atómica y hashing.

Funciones puras sin dependencias del flujo del pipeline: escriben a un archivo
temporal y lo renombran (`os.replace`) para garantizar escritura atómica.
"""

import hashlib
import json
import os
import re

import tomllib


def write_json_atomic(data, path, **kwargs):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, **kwargs)
        f.write("\n")
    os.replace(tmp_path, path)


def write_parquet_atomic(df, path):
    tmp_path = path + ".tmp"
    df.write_parquet(tmp_path)
    os.replace(tmp_path, path)


def pd_excel_writer(path):
    import pandas as pd

    return pd.ExcelWriter(path, engine="xlsxwriter")


def compute_sha256(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_json_if_exists(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_project_version(root_dir):
    pyproject_path = os.path.join(root_dir, "pyproject.toml")
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    version = pyproject_data.get("project", {}).get("version")
    if not version:
        raise SystemExit(f"{pyproject_path} no tiene [project] version")
    return version


def replace_delimited_block(file_path, block_name, new_body, check_only=False, separator="\n\n"):
    """Reemplaza el contenido entre marcadores HTML delimitados por nombre.

    Un marcador ausente es un error duro (a diferencia de un archivo fuente
    que todavía no existe en un checkout fresco): indica un typo o un bloque
    borrado a mano, no un estado esperado del pipeline.

    ``separator`` controla qué va entre los marcadores y el cuerpo:
    ``"\\n\\n"`` (default) para bloques que son su propio párrafo (ej. la
    tabla de datasets); ``"\\n"`` para contenido que debe quedar en su propia
    línea sin línea en blanco (ej. un ítem de lista o un badge, para no
    romper la lista/fila contigua); ``""`` para contenido que debe quedar en
    la MISMA línea que los marcadores (obligatorio dentro de una celda de
    tabla Markdown, que no puede tener saltos de línea reales).
    """
    start_marker = f"<!-- START_{block_name} -->"
    end_marker = f"<!-- END_{block_name} -->"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if start_marker not in content or end_marker not in content:
        raise SystemExit(
            f"ERROR: {file_path} no tiene el bloque delimitado '{block_name}' "
            f"({start_marker} / {end_marker})"
        )

    new_block = f"{start_marker}{separator}{new_body}{separator}{end_marker}"
    pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
    # Reemplazo vía función (no string) para que re.sub no interprete
    # backslashes o \g<...> del cuerpo generado como backreferences.
    new_content = re.sub(pattern, lambda _match: new_block, content, count=1, flags=re.DOTALL)

    if new_content == content:
        return False
    if check_only:
        return True

    tmp_path = file_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    os.replace(tmp_path, file_path)
    return True
