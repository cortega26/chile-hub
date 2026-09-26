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
  doi    = {10.5281/zenodo.22968698},
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

**DOI (concept — todas las versiones):**
[10.5281/zenodo.22968698](https://doi.org/10.5281/zenodo.22968698)

La integración GitHub↔Zenodo está activa: cada release recibe su **version DOI**
automáticamente y el **concept DOI** siempre resuelve a la última versión.
Primeros releases archivados:

| Release | Version DOI |
|:---|:---|
| v1.37.6 | [10.5281/zenodo.22968699](https://doi.org/10.5281/zenodo.22968699) |
| v1.37.7 | [10.5281/zenodo.22969328](https://doi.org/10.5281/zenodo.22969328) |

Pasos seguidos (referencia, ya completados):

1. Cuenta de Zenodo vinculada a GitHub y repositorio `cortega26/chile-hub`
   habilitado en *GitHub → Sync now*.
2. Release normal creado por el CI (`fix`/`feat` → `python-semantic-release`).
3. Zenodo archiva el release y emite version DOI + concept DOI.
4. Concept DOI pegado en `CITATION.cff` (`doi:` + `identifiers`) y en esta
   página. No hace falta mantener nada más: los próximos releases se archivan
   solos.
