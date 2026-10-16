# Embudo de adopción honesto — chile-hub

> **Qué es.** La definición de cómo se mide la adopción de chile-hub sin
> telemetría, solo con contadores públicos, y cómo se refresca antes de la
> revisión de sostenibilidad del **2026-11-01**.
>
> **Qué no es.** No es un objetivo de crecimiento, no es material de difusión y
> no cambia el estado vigente (**HOLD / sin búsqueda activa**, veredicto D
> aceptado 2026-09-30 —
> [`docs/sostenibilidad/README.md`](sostenibilidad/README.md)).
> Existe para que la revisión del 2026-11-01 decida con números fechados en vez
> de cifras vanidosas.
>
> **Método.** [`Auditoría 3, Anexo M`](sostenibilidad/auditoria-3-2026-09-29.md#anexo-m-método-reproducible).
> **Regla anti-drift** ([`AGENTS.md` §12](../AGENTS.md)): ningún número sin
> fecha; el README nunca lleva cifras — se enlazan los reportes vivos
> (`docs/adoption-review.md`, `data/normalized/adoption.json`).

## Etapas (solo contadores públicos, sin telemetría)

| # | Etapa | Contador fuente | Señal que aporta |
|:--:|:---|:---|:---|
| 1 | Actividad de publicación | Descargas PyPI normalizadas por release | Cadencia, **no** adopción |
| 2 | Activación primaria | Descargas del bundle en GitHub Releases | Proxy real de uso de la librería |
| 3 | Adopción espejo | Descargas/likes en Hugging Face | Uso vía `hf://` y subsets |
| 4 | Descubrimiento web | Search Console (impresiones `/comunas/`) | **Sin medir** (ver 107) |
| 5 | Citación downstream | DOI Zenodo / citas | Reúso académico verificable |
| 6 | Usuarios verificados | Tracker manual fuera del repo | Organizaciones con U1–U3 |
| — | Contexto (no es adopción) | Stars/forks, sponsors, dependents, issues de terceros | Ruido de fondo para la revisión |

### 1. Descargas PyPI (siempre normalizadas por release)

- **Fuente:** pypistats (`overall?mirrors=false`) × fechas de release (PyPI JSON).
- **Refresh:**
  ```bash
  curl -s -A "chile-hub-review" "https://pypistats.org/api/packages/chile-hub/overall?mirrors=false"
  curl -s https://pypi.org/pypi/chile-hub/json      # releases → upload_time_iso_8601
  ```
- **Confound conocido:** los releases explican el 94–97% de la varianza diaria
  (≈80–110 descargas por release). Mirrors, CI y bots dominan el resto.
- **Frase permitida (exacta, con fecha):**
  > "Al {fecha}, chile-hub suma {N} descargas en PyPI en los últimos 30 días
  > ({M} releases en el período, ≈{K} por release): mide cadencia de
  > publicación, no usuarios."
- **Prohibido:** "instalaciones", "usuarios", "audiencia" ([`AGENTS.md` §10](../AGENTS.md)).

### 2. Descargas del bundle (activación primaria)

- **Fuente:** GitHub Releases, **paginado** (el `total_downloads` de
  `adoption.json` subcuenta porque el script no pagina — hallazgo Auditoría 3 §0).
- **Refresh:**
  ```bash
  gh api --paginate 'repos/cortega26/chile-hub/releases?per_page=100' \
    --jq '.[].assets[] | select(.name=="chile-hub-publishable-bundle.zip") | .download_count'
  ```
- **Confound conocido:** acumulado histórico, no tasa; sensible a limpieza de
  releases viejos (si el total baja entre revisiones, se reporta la causa, no se
  oculta). La tasa mensual se deriva del delta entre revisiones fechadas.
- **Frase permitida (exacta, con fecha):**
  > "Al {fecha}, el bundle publicable acumula {N} descargas en GitHub Releases
  > ({M} releases con el asset; {D} nuevas desde el {fecha_anterior})."

### 3. Hugging Face (descargas + likes)

- **Fuente:** API pública del dataset espejo (sin auth, sin telemetría).
- **Refresh:**
  ```bash
  curl -s https://huggingface.co/api/datasets/cortega26/chile-hub | jq '{downloads, likes}'
  ```
- **Confound conocido:** HF cuenta re-descargas y CI igual que PyPI; `downloads`
  es ventana móvil, no acumulado propagable sin fecha.
- **Frase permitida (exacta, con fecha):**
  > "Al {fecha}, el espejo de Hugging Face registra {N} descargas y {L} likes."
- **Umbral vigente** (`docs/adoption-review.md`): espejo en Kaggle solo si
  HF ≥ 2× el baseline de forma sostenida.

### 4. Descubrimiento web (sin medir)

- **Fuente prevista:** Google Search Console → Rendimiento → filtrar `/comunas/`
  y `/reference/datasets/`. Requiere registro del sitio por el operador
  (ver [plan 107](../../plans/107-activacion-lanzamiento-handoff.md), Step 1–2).
- **Estado:** `sin dato` hasta que el operador registre la propiedad.
- **Frase permitida (exacta):**
  > "Tráfico de descubrimiento web: sin dato (Search Console no registrado;
  > ver plan 107)."

### 5. Citación downstream (DOI / Zenodo)

- **Fuente:** API de Zenodo (concept DOI + versiones).
- **Refresh:** `docs/adoption-review.md` § "Cómo leer las métricas".
- **Confound conocido:** un DOI publicado no implica reúso; la cita verificable
  es un paper/repo que importe o cite el DOI.
- **Frase permitida (exacta, con fecha):**
  > "Al {fecha}, el concept DOI es {doi} con {V} versiones archivadas y
  > {C} citas downstream verificables."

### 6. Organizaciones con uso verificable (tracker fuera del repo)

- **Fuente:** tracker privado del mantenedor, fuera del repo (Ley 21.719 —
  nunca PII ni términos comerciales en el repo).
- **Definición de "verificado"** (Auditoría 3 §E, rúbrica U/D/W): una
  organización cuenta solo si cumple **U1** (rol declarado en la organización),
  **U2** (artefacto verificable o declaración citable con permiso) y **U3**
  (uso recurrente o parte de un proceso). Nivel actual: **0 al 2026-10-15**.
- **Frase permitida (exacta, con fecha):**
  > "Al {fecha}, hay {N} organizaciones con uso verificable (rúbrica U/D/W,
  > Auditoría 3 §E)."

### Contexto (se registra, no es adopción)

Stars/forks (`gh api repos/cortega26/chile-hub`), sponsors
(`gh api graphql … sponsors`), dependents
(GitHub network + `api.deps.dev`), issues/discussions de terceros. Sirven para
detectar movimiento, no para afirmar uso.

## Procedimiento de refresh (semanal hasta el 2026-11-01)

- **Dueño:** el mantenedor (o el operador con las credenciales listadas abajo).
- **Fechas:** 2026-10-19, 2026-10-26 y revisión del 2026-11-01. Cada refresh
  agrega una entrada fechada al final de `## Registro` en
  [`docs/adoption-review.md`](adoption-review.md) — **nunca** prosa con cifras
  en el README.
- **Pasos:**
  1. Correr los comandos de las etapas 1–3 y 5 + contexto (todos de lectura,
     ninguno modifica nada).
  2. Registrar cada cifra con su fecha y fuente; lo inaccesible queda
     `sin dato` con el motivo — nunca se estima.
  3. Normalizar PyPI por release (etapa 1); derivar la tasa del bundle por delta
     (etapa 2); no presentar ningún contador como usuarios.
  4. Si un hallazgo contradice el veredicto D (p. ej. aparece un usuario
     verificable), se reconcilia explícitamente antes de cambiar el estado
     vigente — por defecto se reporta, no se promueve.
- **Verificación:** `make doctor` → exit 0; el diff solo toca
  `docs/adoption-review.md` (+ cronología en `docs/sostenibilidad/README.md`
  si el refresh registra un análisis nuevo).

## Acciones de operador pendientes (preparadas, no enviadas)

Nada de lo de abajo implica contactar a nadie ni pedir dinero. Son pasos con
credenciales que un agente sin cuentas no puede ejecutar:

1. **Registrar el sitio en Google Search Console** (propiedad prefijo URL
   `https://tooltician.com/chile-hub/`, método etiqueta HTML) y entregar el
   token al repo (plan 107, Step 1) — sin esto la etapa 4 sigue `sin dato`.
2. **Enviar el sitemap** en GSC tras el registro
   (`https://tooltician.com/chile-hub/sitemap.xml`; índice + 3 hijos
   verificados 200 el 2026-10-15).
3. **Revisar Cloudflare Web Analytics** en busca de referrers o dominios
   institucionales (Auditoría 3 §E, Paso 0).
4. **Revisar correo y mensajes directos de LinkedIn** + estado de respuestas a
   los leads #107–#109 (plan 107, Steps 3 y 6).
5. **Responder por escrito la consulta al contador** sobre el vehículo de cobro
   (gate §G, condición 2) — insumo del 2026-11-01, no de este plan.
6. **Los demás pendientes del ROADMAP** (§5/§7: registro Reutilización en
   datos.gob.cl vía ClaveÚnica, solicitud estructurada CEAD, reporte del bulk
   2015 muerto, mesa SGD) siguen como lista de traspaso del mantenedor.

## No-objetivos (lista rechazada, con motivo en una línea)

- **Telemetría en la librería o el sitio:** viola la promesa sin-telemetría del
  pipeline y no la pide ningún usuario.
- **Paywall o datos con muro de pago:** el principio 4 ("lo abierto sigue
  abierto") lo prohíbe; el sponsor no compra datos ni prioridad.
- **Docs en inglés:** sin evidencia de demanda fuera del español; superficie
  especulativa.
- **Kaggle / conda-forge:** diferidos hasta medir HF de forma sostenida
  (umbral: HF ≥ 2× baseline).
- **Sigstore:** hasta que haya un segundo publicador que lo justifique.
- **Tiers, `SPONSORS.md`, patrocinios en landing/README:** HOLD por el gate §G
  (veredicto D vigente).
- **Páginas por región/provincia (SEO programático):** solo con impresiones
  crecientes en Search Console y CTR ≥ 1% (umbral en `adoption-review.md`).
- **Presentar PyPI como instalaciones/usuarios/audiencia:** prohibido por
  [`AGENTS.md` §10](../AGENTS.md); la regresión lo falsó (R² 0,94–0,97).
