# Cómo citar chile-hub

Este proyecto es software abierto (MIT) que **cura y valida datos de fuentes
oficiales**. Si lo usas en un paper, tesis, curso o informe, cita el software y
atribuye además la fuente de cada capa que hayas usado.

> GitHub muestra el botón **"Cite this repository"** automáticamente a partir de
> [`CITATION.cff`](https://github.com/cortega26/chile-hub/blob/main/CITATION.cff).

## Citar el software

**BibTeX** (reemplaza la versión por la que usaste, visible en `pyproject.toml`):

```bibtex
@software{chile_hub,
  title  = {chile-hub: datos públicos de Chile curados y validados},
  author = {Ortega, Carlos},
  year   = {2026},
  url    = {https://tooltician.com/chile-hub/},
  note   = {Versión X.Y.Z}
}
```

**APA 7**:

> Ortega, C. (2026). *chile-hub: datos públicos de Chile curados y validados*
> [Software]. https://tooltician.com/chile-hub/

## Citar una capa específica

chile-hub no es la fuente primaria: es la capa de curación. Cita **la fuente
oficial** (INE, BCN, MINSAL, MINEDUC, MDS, CNE…) y menciona chile-hub como capa
de procesamiento. El semáforo de licencias, la atribución requerida y el enlace
a cada fuente están en
[`DATA_LICENSES.md`](https://github.com/cortega26/chile-hub/blob/main/DATA_LICENSES.md)
y en la ficha de cada capa bajo `docs/datasets/`.

Ejemplo (Censo 2024):

> Instituto Nacional de Estadísticas. (2024). *Censo 2024: población por comuna*
> [Conjunto de datos]. Procesado y validado por chile-hub.
> https://www.ine.gob.cl/

## DOI (Zenodo)

El repositorio está preparado para la integración GitHub↔Zenodo, que emite un
DOI gratuito por cada release. Pasos para el mantenedor (una sola vez):

1. Entrar a [zenodo.org](https://zenodo.org) con la cuenta de GitHub y, en
   *Settings → GitHub*, activar el repositorio `cortega26/chile-hub`.
2. Hacer un release normal (`make release`, que crea el tag y el GitHub Release).
3. Zenodo archiva el release y emite un **concept DOI** (todas las versiones) y
   un **version DOI** (ese release).
4. Pegar el concept DOI en `CITATION.cff` (campo `doi:` + `identifiers`) y en
   esta página; a partir de ahí cada release actualiza el version DOI solo.

Mientras no exista DOI, cita la versión con la URL del repositorio y el número
de versión de `pyproject.toml`.
