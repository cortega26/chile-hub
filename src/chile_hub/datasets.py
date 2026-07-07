"""Enumeración de todos los datasets curados por ChileHub.

Úsalo en vez de strings mágicos para obtener autocompletado en IDE y
detección temprana de errores por typos:

    >>> from chile_hub.datasets import Dataset
    >>> hub.load_polars(Dataset.COMUNAS)
    >>> Dataset.from_string("comunas")
    <Dataset.COMUNAS: 'comunas'>
"""

from __future__ import annotations

import enum
from difflib import get_close_matches


class Dataset(str, enum.Enum):
    """Enumeración de todos los datasets curados por ChileHub.

    Hereda de ``str`` para compatibilidad total: ``Dataset.COMUNAS`` es
    un string ``"comunas"`` en runtime, así que puede pasarse a cualquier
    función que espere ``str``.
    """

    REGIONES = "regiones"
    PROVINCIAS = "provincias"
    COMUNAS = "comunas"
    COMUNAS_ENRIQUECIDAS = "comunas_enriquecidas"
    INDICADORES = "indicadores"
    CENSO_COMUNAL = "censo_comunal"
    CENSO_HOGARES_VIVIENDAS = "censo_hogares_viviendas"
    ESTABLECIMIENTOS_SALUD = "establecimientos_salud"
    ESTABLECIMIENTOS_EDUCACIONALES = "establecimientos_educacionales"
    DISTRITOS_ELECTORALES = "distritos_electorales"
    PARTIDOS_POLITICOS = "partidos_politicos"
    AUTORIDADES_ELECTAS = "autoridades_electas"
    FINANZAS_MUNICIPALES = "finanzas_municipales"
    RESULTADOS_EDUCACIONALES = "resultados_educacionales"
    INDICADORES_URBANOS_SIEDU = "indicadores_urbanos_siedu"
    POBREZA_COMUNAL = "pobreza_comunal"
    CONSUMO_ELECTRICO_COMUNAL = "consumo_electrico_comunal"
    EMPRESAS = "empresas"
    PERFIL_TERRITORIAL_COMUNAL = "perfil_territorial_comunal"

    @classmethod
    def from_string(cls, name: str) -> Dataset:
        """Resuelve un string a Dataset, con sugerencia si no coincide exactamente.

        Args:
            name: Nombre del dataset (ej. ``"comunas"``).

        Returns:
            Miembro de ``Dataset`` correspondiente.

        Raises:
            ValueError: Si el string no coincide con ningún dataset conocido.
        """
        try:
            return cls(name)
        except ValueError:
            matches = get_close_matches(name, [m.value for m in cls], n=1)
            hint = f" Quizás quisiste decir '{matches[0]}'." if matches else ""
            raise ValueError(
                f"Dataset '{name}' no es válido.{hint} Valores posibles: {', '.join(cls.values())}"
            )

    @classmethod
    def values(cls) -> list[str]:
        """Retorna la lista de valores string de todos los datasets.

        Returns:
            Lista de strings con los nombres canónicos de los datasets.
        """
        return [m.value for m in cls]
