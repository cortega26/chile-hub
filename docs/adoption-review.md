# Adoption review — chile-hub

> **Qué es:** el doc de decisión de distribución. Se llena con datos, no con
> impresiones. Cadencia: **primer lunes de cada mes** (o tras un lanzamiento).
> **Regla:** no se agrega superficie nueva sin una señal que la justifique.

## Baseline — 2026-09-26

| Canal | Métrica | Valor | Fuente |
|:---|:---|---:|:---|
| PyPI | Descargas / mes (baseline 2026-09-26, pre-corrección — ver entrada 2026-09-30) | **2.218** | `data/normalized/adoption.json` (semanal, CI) |
| PyPI | Descargas / semana (ídem) | 1.172 | ídem |
| Hugging Face | Descargas / mes | **135** | API HF (`/api/datasets/cortega26/chile-hub`) |
| Hugging Face | Likes | 0 | ídem |
| GitHub | Stars / forks | 90 / 10 | API GitHub |
| GitHub Releases | Descargas de assets | 21 | `adoption.json` |
| Google Search | Impresiones `/comunas/` | **sin dato** (Search Console no registrado) | — |
| Zenodo | DOI publicado | v1.37.6 + v1.37.7; concept `10.5281/zenodo.22968698` | API Zenodo |
| LinkedIn (post 26-sep) | Reacciones / comentarios | 141 / 16 | LinkedIn |

## Cómo leer las métricas (comandos)

```bash
# PyPI + Releases (se refresca solo cada lunes)
cat data/normalized/adoption.json

# Hugging Face
curl -s https://huggingface.co/api/datasets/cortega26/chile-hub \
  | jq '{downloads, likes, lastModified}'

# GitHub
gh api repos/cortega26/chile-hub --jq '{stars: .stargazers_count, forks: .forks_count}'

# Search Console (operador, web): Rendimiento → filtrar /comunas/ y /reference/datasets/
```

## Umbrales de decisión (revisar a las 2–4 semanas)

| Decisión | Señal que la desbloquea | Si NO hay señal |
|:---|:---|:---|
| Profundizar SEO programático (páginas por región/provincia) | `/comunas/` con impresiones crecientes en Search Console y CTR ≥ 1% | No invertir más; el long-tail no está traccionando |
| Espejo en Kaggle | HF ≥ **2×** el baseline (≥ 270 descargas/mes) sostenido | Mantener diferido (ya estaba diferido desde 2026-07-18) |
| Más superficie para agentes (`llms-full.txt`, tools MCP extra) | Evidencia de uso de agentes (consultas MCP reportadas por usuarios, o mención en herramientas) | No construir; el MCP ya cubre el caso base |
| Comparador de comunas como producto | ≥ 3 pedidos explícitos de usuarios distintos (issues/comentarios) | No construir (superficie especulativa) |
| Priorizar capas nuevas por demanda | ≥ 3 issues `dataset_request` con fuente estable y licencia clara | Mantener el foco en profundidad de las capas actuales |
| Playbook de contribución externa | ≥ 1 PR externo mergeado o ≥ 3 contribuyentes activos | No invertir en tooling de contribución todavía |

## Registro

### 2026-09-29 — cierre Plan 129

- `data/normalized/adoption.json` ahora incluye la señal de Hugging Face
  (`huggingface`: `downloads`, `likes`, `lastModified`) leída de la API
  pública del dataset espejo (`https://huggingface.co/api/datasets/cortega26/chile-hub`),
  sin auth y bajo la misma política sin telemetría que el resto del script.
  El umbral de Kaggle de la tabla de arriba (HF ≥ 2× baseline) deja de depender
  de registro manual.
- HF **degrada sola**: si la API falla, la clave queda `null` y el job no
  aborta (el exit 1 sigue anclado a PyPI + GitHub Releases, las fuentes que
  alimentan el badge y la señal base).

### 2026-09-26 — baseline post-lanzamiento

- Se completó la wave de distribución (planes 101–105): HF con 21 subsets,
  JSON-LD + sitemap + `llms.txt`, MCP, 347 páginas por comuna, DOI Zenodo.
- Pipeline diario reparado (permisos `monthly` desde snapshot versionado) y
  cadena release→hf-publish verificada end-to-end.
- Repo aligerado 412→140 MB (ADR-021) para que Zenodo archive rápido.
- Publicado post de seguimiento en LinkedIn (141 reacciones, 16 comentarios) con
  leads concretos registrados en `docs/launch-pack.md` §5.
- **Pendiente de operador:** registrar el sitio en Google Search Console y
  enviar `https://tooltician.com/chile-hub/sitemap.xml` — sin eso, la decisión
  de SEO no se puede tomar con datos.

### 2026-09-26 — revisión (agente)

- PyPI (mes/semana/día): 2218 / 1172 / 32 — fuente: `data/normalized/adoption.json` (generado 2026-09-21)
- HF: descargas 197, likes 0 — fuente: API HF
- GitHub: stars 92, forks 10 — fuente: API GitHub
- Search Console: `sin dato` (pendiente operador)
- Issues de leads: #107, #108, #109 — abiertos y etiquetados
- Schedule diario: falló 23–25 sep (commit 039fc03) — "Build-synced files are stale" en Build and verify data; causa: el gate compara README.md, cuyos conteos cambian con los datos del día y solo los commitea el publish que el gate bloquea (deadlock; sin publish programado desde 2026-08-13; disparador puntual: permisos_edificacion en fallback, corregido en 8d30636). Fix propuesto en plan 108 (branch fix/108-build-synced-stale)
- Notas: sitemap índice + 3 hijos verificados en vivo (200/200/200).

### 2026-09-30 — corrección de la semántica de métricas (Auditoría 3 de sostenibilidad)

- Las "instalaciones PyPI/mes" de este documento son **descargas** y siguen la
  cadencia de releases: una regresión diaria da R²=0,937, con ~93 descargas por
  release (n=101). Tras el cambio de conteo de PyPI del 2026-08-24, el R² sube
  a 0,966. No sirven como medida de usuarios ni de audiencia.
- Proxy de activación de la librería: las descargas de
  `chile-hub-publishable-bundle.zip` en GitHub Releases, que pasaron de 36
  (30-jun) a 119 (29-sep). Eso son ≈ 27 al mes; al 30-sep suman 132.
- `adoption.json.github_releases.total_downloads` subcuenta porque el script no
  pagina `/releases`: reporta 46 cuando el total real es 224 (30-sep).
- 0 dependents (GitHub y deps.dev), 0 issues o discussions de terceros y 0 sponsors.
- Detalle y método reproducible:
  [`docs/sostenibilidad/auditoria-3-2026-09-29.md`](sostenibilidad/auditoria-3-2026-09-29.md)
  (§0 y Anexo M).

### 2026-10-15 — revisión (plan 144, método Anexo M)

Método: [`Auditoría 3, Anexo M`](sostenibilidad/auditoria-3-2026-09-29.md#anexo-m-método-reproducible).
Definiciones y frases permitidas: [`docs/adoption-funnel.md`](adoption-funnel.md)
(creado en este plan). Resto del plan 107 ejecutado dentro del tope §E
(GSC saltado sin token; sitemap, issues y schedule verificados abajo).

- PyPI: 6.638 descargas `without_mirrors` en 30 días (2026-09-15 → 2026-10-14,
  pypistats) con 61 releases en el período → ≈109 por release. Sigue midiendo
  cadencia, no usuarios. `data/normalized/adoption.json` (generado 2026-10-12):
  mes 4.225 / semana 1.859 / día 98.
- Bundle: **169** descargas acumuladas en GitHub Releases (80 releases con el
  asset `chile-hub-publishable-bundle.zip`, API paginada hoy). Discrepancia
  honesta: al 30-sep se citó un total real de 224; el acumulado de hoy es menor,
  consistente con limpieza posterior de releases/assets viejos (causa no
  verificada — no se afirma crecimiento contra el 30-sep; la tasa se deriva por
  delta entre revisiones futuras).
- HF: 444 descargas, 0 likes — fuente: API HF (`lastModified` 2026-10-13).
  (26-sep: 197; `adoption.json` 12-oct: 387.)
- GitHub: stars 129, forks 12 — fuente: API GitHub. (Baseline 26-sep: 90/10.)
- Tráfico del repo (solo mantenedor, no citable externamente): 166 vistas /
  98 únicos en 14 días — fuente: `traffic/views`.
- Dependents: 0 (GitHub network + deps.dev v1.49.2). Sponsors: 0.
  Issues/discussions de terceros: 0.
- Search Console: `sin dato` (pendiente operador — plan 107, Step 1 saltado sin
  token de GSC).
- Issues de leads: #107, #108, #109 — OPEN con labels `enhancement,dataset`.
- Zenodo: `sin dato` (API sin respuesta el 2026-10-15; concept DOI vigente
  `10.5281/zenodo.22968698`, sin citas downstream verificadas conocidas).
- Schedule diario: 2026-10-15 `success` + `Publish verified data: success`.
  (10-14 `failure` — `log-failed` sin líneas de error visibles, no se investiga
  en este plan; 10-13 `cancelled`.)
- Notas: sitemap índice + 3 hijos en 200/200/200; veredicto D sin cambios
  (0 organizaciones verificables, PyPI = cadencia). Etiqueta del badge
  `adoption_badge.json` ("instalaciones/mes") sigue pendiente de corrección —
  hallazgo ya registrado en Auditoría 3 §0, fuera del alcance de este plan.
- Horas plan 144 (tope §E 15 h): baseline 0,3 + refresh Anexo M y checks
  107 (Steps 2–4) 0,5 + `adoption-funnel.md` 0,5 + este refresh 0,3 ≈ **1,6 h**.
  Acciones con credenciales preparadas como lista de traspaso, no enviadas
  (`adoption-funnel.md` § Acciones de operador).

### 2026-10-26 — Search Console registrado

- **Propiedades verificadas** en la misma cuenta de Google: prefijo
  `https://tooltician.com/chile-hub/` y dominio `tooltician.com`. Google verificó
  automáticamente vía *proveedor de nombres de dominio*: el registro
  `TXT google-site-verification=…` quedó en el apex de `tooltician.com`,
  comprobado por API de Cloudflare y por DNS público (`1.1.1.1`). Ese registro no
  debe borrarse; sin él se pierde la verificación.
- **Nada nuevo en el repo:** no hay token ni archivo de verificación que rotar. El
  método de archivo HTML y la etiqueta meta se descartaron al quedar la propiedad
  verificada por DNS.
- **Sitemap: ya estaba enviado desde el 2026-09-26**, antes de esta sesión —no
  era una acción pendiente, contrario a lo que decía este documento—. Estado
  *Correcto*, última lectura **2026-10-18**, **473 URLs descubiertas**. El índice
  y sus 3 hijos (`sitemap-pages.xml`, `reference/sitemap.xml`,
  `comunas/sitemap.xml`) responden 200 el 2026-10-26. Reenviarlo se rechaza por
  duplicado: no hay nada que corregir.
- **Lecturas de rendimiento:** ninguna todavía; el panel arranca vacío. El primer
  dato de impresiones exige ≥2 semanas de histórico, y la lectura automatizada
  (cuenta de servicio) sigue sin implementar. Las 473 URLs son
  **descubrimiento**, no tráfico: no se presentan como visitas.
- **Efecto en el veredicto D:** ninguno. Registrar el instrumento no crea demanda;
  mientras no haya impresiones y clics, "descubrimiento orgánico" sigue sin dato.
