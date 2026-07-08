# Contribuir

Gracias por ayudar a mantener chile-hub confiable.

## Verificaciones Locales

Ejecuta las verificaciones útiles más pequeñas antes de abrir un pull request:

```bash
make lint
make format-check
make test
make doctor
```

`make doctor` corre `scripts/check_companion_paths.py registry`: verifica que cada
dataset de `data/dataset_catalog_config.json` tenga su contrato en
`contracts/datasets/` y su doc en `docs/datasets/`. En CI, un chequeo adicional por
pull request (`check_companion_paths.py companions`) exige que ciertos cambios de
código (`src/validation.py`, `src/extractors/**`, `data/dataset_catalog_config.json`,
entre otros — ver `AGENTS.md §12`) vengan acompañados de su test o documento
asociado en el mismo diff. Si CI marca una ruta compañera faltante, actualiza el
doc/test indicado en el mismo PR.

Para cambios que afectan archivos públicos generados, ejecuta:

```bash
make build
make verify
make verify-landing
```

## Cambios de Datos

Los nuevos conjuntos de datos deben seguir `AGENTS.md`: evalúa los derechos de la fuente primero, agrega un extractor, escribe metadatos de staging, valida en `src/validation.py`, conecta la compilación, agrega pruebas, actualiza CI y documenta el conjunto de datos.

Nunca edites `data/normalized/` manualmente. Regenera los datos a través del pipeline.

## Pull Requests

Usa prefijos de commits convencionales en los títulos de los commits cuando sea posible, como `fix:`, `feat:`, `docs:` o `chore:`. Los lanzamientos se generan a partir del historial de commits después de que el pipeline completo pase.
