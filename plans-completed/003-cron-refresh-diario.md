# Plan 003: Agregar cron diario para refresh automático de datos

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar. Si algo en "Condiciones de STOP" ocurre, detente y reporta — no improvises.
>
> **Drift check (ejecutar primero)**: `git diff --stat e3951f0..HEAD -- .github/workflows/pipeline-check.yml`
> Si el workflow cambió desde que se escribió este plan, compara con los excerpts antes de continuar.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: M
- **Riesgo**: MED
- **Depende de**: 002 (el cache de CI reduce el costo del cron diario)
- **Categoría**: direction/dx
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

Los indicadores económicos (UF, dólar, euro, UTM, IPC) se actualizan diariamente. La política de frescura del dataset `indicadores` declara `max_age_hours: 72`, pero sin un cron no hay refresh automático — el hub solo se actualiza cuando alguien hace push manualmente. Esto contradice la promesa central del producto. El código de AGENTS.md §9 ya tiene el YAML exacto documentado como "pendiente". Este plan lo activa.

El riesgo a gestionar: si el cron job hace commit de los artefactos generados, ese commit puede disparar un nuevo run del workflow (loop infinito). La solución es separar el job de refresh del job de publicación, o usar una condición que evite re-disparar en commits del bot.

## Estado actual

Archivo: `.github/workflows/pipeline-check.yml`

```yaml
# líneas 1-6 (estado actual — trigger solo en push y PR)
name: Pipeline Check

on:
  push:
  pull_request:
```

AGENTS.md §9 documenta el YAML pendiente:

```yaml
# AGENTS.md:357-360
on:
  push:
  pull_request:
  schedule:
    - cron: '0 10 * * *'   # 06:00 CLT (UTC-4) todos los días
```

El workflow actual tiene un único job `verify-pipeline` que: extrae, construye, verifica, testea, genera status, publica summary y sube el bundle como artifact de CI. El bundle se sube con `actions/upload-artifact@v4` pero **no se commitea al repo** — los artefactos de CI son temporales.

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Validar YAML | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml')); print('OK')"` | `OK`, exit 0 |
| Ver trigger actual | `grep -A5 "^on:" .github/workflows/pipeline-check.yml` | muestra trigger |

## Alcance

**En scope**:
- `.github/workflows/pipeline-check.yml` — agregar el trigger `schedule` y ajustar condiciones si hace falta

**Fuera de scope**:
- No agregar un nuevo workflow separado (si el ejecutor considera que hace falta uno por separado, es condición de STOP)
- No modificar ningún archivo fuente en `src/` o `scripts/`
- No configurar GitHub Secrets ni tokens adicionales

## Git workflow

- Rama: `advisor/003-cron-refresh-diario`
- Estilo de commit: `feat: agregar cron diario para refresh automatico de indicadores`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Agregar el trigger `schedule` al workflow

Modificar la sección `on:` del workflow para agregar el cron:

```yaml
on:
  push:
  pull_request:
  schedule:
    - cron: '0 10 * * *'   # 06:00 CLT (UTC-4) todos los días
```

**Verificar**: `grep -A6 "^on:" .github/workflows/pipeline-check.yml` muestra el cron.

### Paso 2: Agregar condición para evitar loops de commits

Si el cron job genera datos y en el futuro se decide commitear esos datos al repo (no es el caso ahora — el bundle se sube solo como artifact de CI), se necesitará una condición. **En el estado actual el workflow no commitea nada**, por lo que el loop no ocurre. Sin embargo, agregar una condición preventiva es buena práctica:

En el job `verify-pipeline`, verificar si ya tiene una condición `if:`. Si no la tiene, agregar:

```yaml
jobs:
  verify-pipeline:
    runs-on: ubuntu-latest
    if: github.event_name != 'push' || !contains(github.event.head_commit.message, '[skip ci]')
```

Esta condición permite correr en schedule (siempre), en push (salvo que el mensaje contenga `[skip ci]`), y en PR (siempre).

**Verificar**: `grep -A2 "verify-pipeline:" .github/workflows/pipeline-check.yml` muestra el `if:` si fue agregado.

**Nota importante**: Si el ejecutor ve que el workflow ya tiene alguna condición `if:` en el job, reportar el estado actual antes de modificar. No sobrescribir condiciones existentes.

### Paso 3: Validar YAML

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml')); print('OK')"
```

**Verificar**: `OK`, exit 0.

### Paso 4: Confirmar que el trigger de schedule aparece correctamente

```bash
grep -n "schedule\|cron" .github/workflows/pipeline-check.yml
```

**Verificar**: aparecen las líneas del schedule con el cron `0 10 * * *`.

## Plan de tests

No aplica directamente — el cron se verifica cuando CI lo ejecuta. Para forzar un test local:

```bash
# Simular que el workflow se dispara (solo valida sintaxis y lógica local):
python3 -c "import yaml; d = yaml.safe_load(open('.github/workflows/pipeline-check.yml')); print('triggers:', list(d['on'].keys()))"
```

Esperado: `triggers: ['push', 'pull_request', 'schedule']`

## Criterios de done

- [ ] `grep "schedule" .github/workflows/pipeline-check.yml` retorna match
- [ ] `grep "0 10 \* \* \*" .github/workflows/pipeline-check.yml` retorna match
- [ ] `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml'))"` sale con exit 0
- [ ] Solo `.github/workflows/pipeline-check.yml` modificado
- [ ] `plans/README.md` fila de estado actualizada a DONE

## Condiciones de STOP

- Si el workflow ya tiene lógica que implica que el cron podría commitear datos (revisar todos los steps — si alguno hace `git push` o `git commit`, es condición de STOP y hay que diseñar la separación de jobs primero).
- Si la validación YAML falla.
- Si el ejecutor considera necesario crear un workflow separado para el cron — reportar en lugar de improvisar.

## Notas de mantenimiento

- El cron corre a las 10:00 UTC = 06:00 CLT (UTC-4 en verano). En invierno CLT es UTC-3, por lo que el cron corre a las 07:00 CLT. Ajustar si se requiere hora exacta estacional.
- Si en el futuro el pipeline commitea los artefactos generados al repo (ej. para GitHub Pages), agregar una condición `[skip ci]` en los commits del bot y ajustar el `if:` del job para filtrar esos commits correctamente.
- Los artefactos actuales solo se suben como artifact de CI (`actions/upload-artifact`), no se commitean — el loop no es un problema hoy.
