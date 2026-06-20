"""Helpers de entrada/salida atómica y hashing.

Funciones puras sin dependencias del flujo del pipeline: escriben a un archivo
temporal y lo renombran (`os.replace`) para garantizar escritura atómica.
"""

import hashlib
import json
import os


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
