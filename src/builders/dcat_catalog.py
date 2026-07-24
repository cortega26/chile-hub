"""Generacion del catalogo DCAT-US (data.json) desde el datapackage.json.

Prototipo de descubribilidad (ver ADR-010): traduce el descriptor Frictionless
ya publicado a un catalogo estilo DCAT-US (perfil de data.gov, dataset[] +
distribution[]), la fuente que cosechan la mayoria de los portales de datos
abiertos gubernamentales basados en CKAN. NO reemplaza datapackage.json (sigue
siendo la fuente de verdad tecnica); este archivo solo se deriva de el, nunca se
edita a mano.
"""

import os

from src.builders._shared import NORMALIZED_DIR
from src.builders.io_utils import write_json_atomic


def build_dcat_catalog(data_package):
    """Construye el dict del catalogo DCAT-US desde el dict de datapackage.json."""
    base_url = data_package.get("homepage", "").rstrip("/")
    modified = data_package.get("created", "")

    datasets = []
    for resource in data_package.get("resources", []):
        license_url = ""
        licenses = resource.get("licenses") or []
        if licenses:
            license_url = licenses[0].get("path", "")

        download_url = f"{base_url}/data/normalized/{resource['path']}"
        distribution = {
            "downloadURL": download_url,
            "mediaType": resource.get("mediatype", ""),
            "format": resource.get("format", ""),
            "title": resource.get("title", resource["name"]),
        }

        dataset = {
            "identifier": resource["name"],
            "title": resource.get("title", resource["name"]),
            "description": resource.get("description", ""),
            "modified": modified,
            "distribution": [distribution],
        }
        if license_url:
            dataset["license"] = license_url
        datasets.append(dataset)

    return {
        "title": data_package.get("title", "chile-hub"),
        "description": data_package.get("description", ""),
        "homepage": data_package.get("homepage", ""),
        "dataset": datasets,
    }


def write_dcat_catalog_json(data_package):
    """Genera y escribe data/normalized/data.json. Retorna la ruta."""
    catalog = build_dcat_catalog(data_package)
    output_path = os.path.join(NORMALIZED_DIR, "data.json")
    write_json_atomic(catalog, output_path, ensure_ascii=False, indent=2)
    return output_path
