# Valor demostrable: tres cruces territoriales reproducibles

> **Objetivo:** permitir que un investigador, desarrollador o evaluador compruebe
> resultados con datos reales y una auditoría de procedencia, sin depender del autor.
> Esto **no** es una prueba de adopción ni una comparación de rendimiento externa.
>
> **Fecha de diseño:** 2026-10-16. **Código:** [`scripts/proof_of_value.py`](../scripts/proof_of_value.py).
> **Fuente del producto:** [`docs/product-spec.md`](product-spec.md) y
> [ADR-023](adr/ADR-023-posicionamiento-ultima-milla-no-portal.md).

## Prueba en un comando

Desde un clon del repositorio (Python 3.11–3.14, **sin instalar dependencias**
ni descargar nuevas fuentes):

```bash
python scripts/proof_of_value.py --runs 5 --output /tmp/chile-hub-value-proof.json
```

Se puede ejecutar desde cualquier directorio: la ruta por defecto se resuelve
con relación al archivo del script. Usa los artefactos **ya versionados** bajo
`data/normalized/`; no toca el pipeline, no hace llamadas de red, no envía
telemetría y no modifica `data/normalized/`.

La salida de consola incluye por caso comunas cruzadas, porcentaje de cobertura
y mediana de cinco repeticiones. El JSON contiene además fecha UTC de ejecución,
SHA del commit Git (si está disponible), versión de Python, plataforma, SHA-256 y
tamaño de cada dataset de entrada, hash de cada resultado y la observación de
limitaciones. **Comparar `resultado_sha256` entre máquinas** permite verificar
el resultado con los mismos archivos de entrada; no comparar tiempos entre
máquinas distintas como si fueran una aceleración demostrada.

```bash
python -m unittest discover -s tests -p 'test_proof_of_value.py' -v
# o: pytest tests/test_proof_of_value.py -q
```

## Qué demuestra realmente

| Caso | Entradas normalizadas | Evidencia | Qué NO demuestra |
|:---|:---|:---|:---|
| 1. Población de 65+ por comuna | `comunas` + `censo_comunal` | Unicidad CUT, cobertura del cruce, un ranking descriptivo Censo 2024 | Que el tiempo ahorrado frente a INE sea X horas |
| 2. Hogares/viviendas por región | `comunas` + `censo_hogares_viviendas` | Unicidad CUT, agregación por 16 regiones, recuentos Censo 2024 | Que hogares = viviendas |
| 3. Perfil territorial + pobreza | `perfil_territorial_comunal` + `pobreza_comunal` | Cobertura de pobreza por ingresos SAE 2022; lista exacta de claves faltantes | Que la pobreza 2022 sea simultánea al Censo 2024 o explique sus resultados |

**Lectura del snapshot verificado el 2026-10-16** (`main@605482f`):
346/346 comunas en cruces 1 y 2; 345/346 en el tercero; la clave
`12202` no figura en la capa de pobreza 2022. Estos conteos describen
**ese snapshot**, no son un compromiso permanente. El script recalcula
y deja constancia del estado **al momento de su ejecución**.

Las tasas de pobreza son estimaciones SAE del Ministerio de Desarrollo Social
y Familia (año 2022); la población del caso 3 es del Censo 2024 del INE.
No sumar ni interpretar las variables de años distintos como si fueran un panel
temporal consistente.

## Matriz de diferenciación comprobable

| Propuesta de valor | Prueba interna disponible | Estado de comparación externa |
|:---|:---|:---|
| Claves territoriales interoperables | Contratos `contracts/datasets/` + cruces 1–3 con cobertura | Sin benchmark controlado contra otros proveedores |
| Transparencia de datos ausentes | `cut_sin_cruce` y `cut_fuera_de_base` en el resultado | Sin comparación auditada |
| Reproducibilidad de análisis | Hash SHA-256 de entradas y de salidas + commit Git | Reproducibilidad computacional local, no replicación científica externa |
| Procedencia, calidad y licencia por capa | `data/normalized/provenance_report.md`, `dataset_quality.json`, `DATA_LICENSES.md` | No se ha demostrado exclusividad |
| Acceso listo para Python/SQL | API, CLI, Parquet y notebook existentes | No es una función exclusiva; no reclamar unicidad |

**Regla de posicionamiento:** no presentar ninguna fila como un *moat* exclusivo
ni usar superlativos del tipo «más rápido», «único» o «mejor que» sin medición
independiente, fuentes verificables y tareas equivalentes.

## Protocolo para una comparación futura justa

1. Definir **antes** las tareas, la fecha/corte de datos, los campos, el hardware,
   la experiencia del operador y el criterio de éxito. Se necesitan conjuntos
   comparables y referencias precisas a las fuentes primarias.
2. Medir por separado: *tiempo hasta resultado correcto*, pasos manuales,
   cobertura y errores de join, rastreabilidad, reproducción por otro operador.
   Registrar arranque en frío y caché caliente por separado.
3. Repetir al menos cinco veces las operaciones automatizadas y publicar los
   comandos y salidas, incluyendo fallos. Una observación humana de flujo manual
   no se presenta como benchmark estadístico.
4. Incorporar los mejores caminos disponibles **de cada solución**. No comparar
   el camino optimizado de chile-hub con el camino más torpe de otra herramienta.
5. Publicar una tabla *solo cuando* existan resultados replicados por terceros.
   «Sin medir» no es «pierde la competencia».

## De prueba a uso externo (14 días, sin nueva infraestructura)

- **Días 1–3:** ejecución del script, tests y validación del JSON en otra máquina;
  corregir cualquier inconsistencia real; capturar el SHA de commit. No construir
  un nuevo explorador, API, MCP ni una copia de Zenodo: ya existen.
- **Días 4–7:** mostrar el caso 1 en un Colab existente
  ([notebook 01](../examples/notebooks/01_comunas_censo.ipynb)) y enlazar este
  protocolo, evitando promesas de duración no medidas. Un usuario nuevo debe
  poder completar y explicar el cruce sin el mantenedor.
- **Días 8–10:** solicitar pruebas voluntarias **solo a interesados que hayan
  aceptado recibirlas**; registrar si completaron, fricciones y errores
  reportados, sin capturar PII públicamente. Metas de experimento: 5 pruebas
  externas y 3 reproducciones autónomas; **no son resultados obtenidos**.
- **Días 11–14:** contrastar resultados externos y priorizar una sola mejora
  que elimine la fricción dominante. Preparar una demostración corta con fuente,
  limitación y archivo reproducible. Si nadie prueba, documentar 0, no crear
  más funcionalidades por intuición.

**Límites del mantenedor:** máximo 3 horas propias de supervisión por semana,
sin suscripciones nuevas ni outreach automático. Nada al control-plane.
Ian: entregar el dataset versionado personalmente si corresponde; una futura
cita en un paper es señal **solo después de comprobar publicación y referencia**.
UDD: no insistir antes del contacto previsto en noviembre.

La revisión de sostenibilidad del **2026-11-01** sigue en
[`docs/sostenibilidad/README.md`](sostenibilidad/README.md): HOLD vigente.
Esta prueba no autoriza pedir patrocinios ni postular a fondos sin superar
los gates de evidencia existentes.
