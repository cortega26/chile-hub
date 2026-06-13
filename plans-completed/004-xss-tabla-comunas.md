# Plan 004: Corregir XSS en tabla de comunas de la landing

> **Instrucciones para el ejecutor**: Sigue este plan paso a paso. Ejecuta cada comando de verificación y confirma el resultado esperado antes de avanzar.
>
> **Drift check (ejecutar primero)**: `git diff --stat e3951f0..HEAD -- index.html`
> Si `index.html` cambió, compara el excerpt de "Estado actual" con el archivo real antes de continuar.

## Estado

- **Prioridad**: P1
- **Esfuerzo**: S
- **Riesgo**: LOW
- **Depende de**: ninguno
- **Categoría**: security
- **Planeado en**: commit `e3951f0`, 2026-06-12

## Por qué importa

La función `renderTable()` en `index.html` construye filas de la tabla de comunas usando `tr.innerHTML` con template literals que insertan directamente propiedades de los objetos del JSON (`c.codigo_comuna`, `c.nombre_comuna`, etc.) sin escapar. Si el JSON de comunas contuviera HTML o JavaScript malicioso — por ejemplo, por una comprometización del pipeline de build o del servidor que lo sirve — ese código se ejecutaría en el navegador de todos los visitantes. La función `escapeHtml()` ya existe en el mismo archivo (línea 1128) y se usa correctamente en el resto de la landing. Este fix cierra el gap de consistencia.

## Estado actual

Archivo: `index.html`

Función `escapeHtml` ya definida en el archivo (línea 1128):

```javascript
// index.html:1128-1136
function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
```

Código vulnerable actual (líneas 1781–1790):

```javascript
// index.html:1781-1790 — VULNERABLE: innerHTML con variables sin escapar
paginatedRows.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td><span class="comuna-code">${c.codigo_comuna}</span></td>
        <td style="font-weight: 500; color: var(--text-primary);">${c.nombre_comuna}</td>
        <td>${c.nombre_provincia}</td>
        <td>${c.nombre_region}</td>
        <td>${formatNum.format(c.poblacion_estimada)}</td>
        <td style="font-size: 0.85rem; font-family: monospace;">${c.latitud_cabecera.toFixed(4)}, ${c.longitud_cabecera.toFixed(4)}</td>
    `;
    tableBody.appendChild(tr);
});
```

Patrón correcto ya usado en otras partes del archivo (ejemplo, línea 1242):

```javascript
// index.html:1242 — patrón correcto
<a class="dataset-action" href="${escapeHtml(path)}" target="_blank" rel="noopener noreferrer">
```

## Comandos necesarios

| Propósito | Comando | Esperado en éxito |
|---|---|---|
| Verificar que escapeHtml existe | `grep -n "function escapeHtml" index.html` | retorna línea con la definición |
| Verificar el bloque vulnerable | `grep -n "codigo_comuna\|nombre_comuna\|nombre_provincia\|nombre_region" index.html \| grep -v "escapeHtml"` | tras el fix, no debe haber líneas dentro de innerHTML sin escapeHtml |
| Smoke test landing | `.venv/bin/python scripts/verify_landing.py` | exit 0 |

## Alcance

**En scope**:
- `index.html` — solo el bloque `tr.innerHTML` de la función `renderTable` (alrededor de líneas 1781–1790)

**Fuera de scope**:
- No modificar la función `escapeHtml` ni ningún otro bloque del archivo
- No cambiar la lógica de paginación ni filtrado de la tabla

## Git workflow

- Rama: `advisor/004-xss-tabla-comunas`
- Estilo de commit: `fix: escapar variables en innerHTML de tabla de comunas`
- No hacer push ni abrir PR salvo instrucción explícita.

## Pasos

### Paso 1: Localizar el bloque exacto

```bash
grep -n "tr.innerHTML" index.html
```

Anotar la línea. Debe estar alrededor de la 1783.

### Paso 2: Aplicar el fix — envolver las 4 variables de texto en `escapeHtml()`

Reemplazar el bloque `tr.innerHTML` actual con:

```javascript
    tr.innerHTML = `
        <td><span class="comuna-code">${escapeHtml(c.codigo_comuna)}</span></td>
        <td style="font-weight: 500; color: var(--text-primary);">${escapeHtml(c.nombre_comuna)}</td>
        <td>${escapeHtml(c.nombre_provincia)}</td>
        <td>${escapeHtml(c.nombre_region)}</td>
        <td>${formatNum.format(c.poblacion_estimada)}</td>
        <td style="font-size: 0.85rem; font-family: monospace;">${c.latitud_cabecera.toFixed(4)}, ${c.longitud_cabecera.toFixed(4)}</td>
    `;
```

Nota: `c.poblacion_estimada` pasa por `formatNum.format()` (que convierte a string formateado) — ya es seguro porque `Intl.NumberFormat.format()` no produce HTML. `c.latitud_cabecera.toFixed(4)` y `c.longitud_cabecera.toFixed(4)` son operaciones numéricas que producen strings de dígitos y punto decimal — también seguros. Solo las 4 propiedades de string de texto necesitan `escapeHtml()`.

**Verificar**:

```bash
grep -n "codigo_comuna\|nombre_comuna\|nombre_provincia\|nombre_region" index.html | grep "innerHTML" | grep -v "escapeHtml"
```

Debe devolver cero líneas (todas las ocurrencias dentro de innerHTML ya usan escapeHtml).

### Paso 3: Correr el smoke test de la landing

```bash
.venv/bin/python scripts/verify_landing.py
```

**Verificar**: exit 0, sin errores.

## Plan de tests

No se escriben nuevos tests unitarios para este fix (es HTML/JS). El smoke test de Playwright en `scripts/verify_landing.py` verifica que la tabla carga y es visible. Si en el futuro se agregan tests de contenido de la tabla en `verify_landing.py`, incluir una aserción que verifique que el texto de una comuna conocida aparece correctamente sin caracteres HTML escapados visibles.

## Criterios de done

- [ ] `grep -n "tr.innerHTML" index.html` muestra el bloque con `escapeHtml()` en las 4 propiedades de texto
- [ ] `grep -n "codigo_comuna\|nombre_comuna\|nombre_provincia\|nombre_region" index.html | grep "innerHTML" | grep -v escapeHtml` devuelve vacío
- [ ] `.venv/bin/python scripts/verify_landing.py` sale con exit 0
- [ ] Solo `index.html` modificado
- [ ] `plans/README.md` fila de estado actualizada a DONE

## Condiciones de STOP

- Si `grep -n "function escapeHtml" index.html` devuelve vacío — la función fue eliminada o renombrada. No continuar; reportar.
- Si el smoke test falla después del fix — deshacer el cambio y reportar el error exacto.

## Notas de mantenimiento

- Si en el futuro se agrega una nueva columna a la tabla de comunas, recordar envolver la nueva expresión de string en `escapeHtml()`.
- La función `escapeHtml` en este archivo es ad-hoc. Si el proyecto adopta un framework JS, reemplazarla por el mecanismo nativo del framework (que hace esto automáticamente).
