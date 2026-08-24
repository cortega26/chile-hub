"""Registry de DatasetSpec — piloto de migración incremental (Phase 2).

Contiene el modelo tipado ``DatasetSpec``, su loader fail-closed y las
proyecciones de compatibilidad hacia las representaciones legacy. El único
spec autorizado hoy es el piloto ``partidos_politicos`` (ver
``docs/architecture-migration-phase-2-pilot.md``).
"""

from .dataset_spec import (
    DatasetSpec,
    DatasetSpecError,
    catalog_config_with_spec_overlay,
    has_spec,
    iter_specs,
    load_dataset_spec,
    parse_dataset_spec,
    source_registry_with_spec_overlay,
)

__all__ = [
    "DatasetSpec",
    "DatasetSpecError",
    "catalog_config_with_spec_overlay",
    "has_spec",
    "iter_specs",
    "load_dataset_spec",
    "parse_dataset_spec",
    "source_registry_with_spec_overlay",
]
