# Plan 002: Agregar caché de pip y Playwright en CI

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar. Si algo en "Condiciones de STOP" ocurre, detente y reporta.
>
> **Drift check (ejecutar primero)**: `git diff --stat e3951f0..HEAD -- .github/workflows/pipeline-check.yml`
> Si el workflow cambió desde que se escribió este plan, compara con los excerpts antes de continuar.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: S
- **Riesgo**: LOW
- **Depende de**: 001 (idealmente; el caché de pip toma como clave `requirements.txt`, que 001 estabiliza)
- **Categoría**: perf/dx
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

Cada run de CI reinstala desde cero ~800 MB de paquetes Python más el binario de Chromium (~200 MB). En un repositorio de pipeline de datos con pushes frecuentes, esto agrega 3–5 minutos innecesarios por run. Con `cache: pip` en `setup-python` y un cache para Playwright, la mayor parte de ese tiempo desaparece en runs que no cambian dependencias (la mayoría).

## Estado actual

Archivo: `.github/workflows/pipeline-check.yml`

```yaml
# líneas 14-26 (estado actual)
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Install Chromium for landing verification
      run: python -m playwright install --with-deps chromium
```

No hay ningún `actions/cache` ni `cache: pip` en el archivo. El resto del workflow (extractores, build, verify, tests, landing, status, summary, upload artifact) no se toca.

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Validar YAML | `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml'))"` | exit 0 sin output |
| Ver workflow actual | `cat .github/workflows/pipeline-check.yml` | muestra contenido |

## Alcance

**En scope**:
- `.github/workflows/pipeline-check.yml` — solo las secciones de setup de Python e instalación de deps

**Fuera de scope**:
- Cualquier otro paso del workflow (extractores, build, tests, landing, artifact upload, etc.)

## Git workflow

- Rama: `advisor/002-cache-ci`
- Estilo de commit: `feat: agregar cache de pip y Playwright en CI para reducir tiempo de build`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Agregar `cache: pip` al step de setup-python

Modificar el step "Set up Python" para incluir el parámetro `cache`:

```yaml
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"
        cache: pip
```

`cache: pip` en `actions/setup-python@v5` usa `requirements.txt` como cache key automáticamente. No requiere `actions/cache` separado.

**Verificar**: `grep -A4 "Set up Python" .github/workflows/pipeline-check.yml` muestra `cache: pip`.

### Paso 2: Agregar cache para Playwright/Chromium

Insertar un nuevo step entre "Install dependencies" y "Install Chromium for landing verification":

```yaml
    - name: Cache Playwright browsers
      uses: actions/cache@v4
      with:
        path: ~/.cache/ms-playwright
        key: playwright-chromium-${{ runner.os }}-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          playwright-chromium-${{ runner.os }}-
```

El path `~/.cache/ms-playwright` es donde Playwright almacena los binarios en Linux (el runner de CI es ubuntu-latest).

**Verificar**: `grep -A6 "Cache Playwright" .github/workflows/pipeline-check.yml` muestra la sección completa.

### Paso 3: Cambiar el step de Chromium a instalación condicional

El step existente `python -m playwright install --with-deps chromium` aún debe ejecutarse (para que el cache se llene en el primer run y para instalar deps del sistema). No cambia:

```yaml
    - name: Install Chromium for landing verification
      run: python -m playwright install --with-deps chromium
```

Esto es correcto — Playwright detecta si el binario ya está en caché y evita la descarga. No se necesita cambio aquí.

**Verificar**: El step "Install Chromium" sigue presente sin cambios.

### Paso 4: Validar la sintaxis YAML del workflow

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml')); print('OK')"
```

**Verificar**: imprime `OK`, exit 0.

### Paso 5: Verificar que el orden de steps es correcto

```bash
grep -n "name:" .github/workflows/pipeline-check.yml
```

**Verificar**: el orden es:
1. Checkout repository
2. Set up Python ← con `cache: pip`
3. Install dependencies
4. Cache Playwright browsers ← nuevo
5. Install Chromium for landing verification
6. Run extractors
7. ...resto sin cambios

## Plan de tests

No aplica — este plan modifica infraestructura CI. La verificación es que el workflow sea YAML válido y que los tests existentes sigan pasando cuando CI corra.

## Criterios de done

- [ ] `grep "cache: pip" .github/workflows/pipeline-check.yml` retorna match
- [ ] `grep "ms-playwright" .github/workflows/pipeline-check.yml` retorna match
- [ ] `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/pipeline-check.yml'))"` sale con exit 0
- [ ] Solo `.github/workflows/pipeline-check.yml` modificado (`git status`)
- [ ] `plans/README.md` fila de estado actualizada a DONE

## Condiciones de STOP

- Si `actions/setup-python@v5` no soporta `cache: pip` (verificar en la documentación de la action antes de commitear).
- Si la validación YAML falla después de editar.
- Si hay lógica condicional existente en el workflow que haga al orden de steps sensible — reportar antes de cambiar.

## Notas de mantenimiento

- Si `requirements.txt` cambia, el cache de pip se invalida automáticamente (la key incluye el hash del archivo).
- Si se cambia la versión de Python en CI, el cache también se invalida automáticamente.
- Si se migra de ubuntu-latest a otro runner, verificar que `~/.cache/ms-playwright` siga siendo el path correcto para Playwright.
