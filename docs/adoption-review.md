# Adoption review — chile-hub

> **Qué es:** el doc de decisión de distribución. Se llena con datos, no con
> impresiones. Cadencia: **primer lunes de cada mes** (o tras un lanzamiento).
> **Regla:** no se agrega superficie nueva sin una señal que la justifique.

## Baseline — 2026-09-26

| Canal | Métrica | Valor | Fuente |
|:---|:---|---:|:---|
| PyPI | Instalaciones / mes | **2.218** | `data/normalized/adoption.json` (semanal, CI) |
| PyPI | Instalaciones / semana | 1.172 | ídem |
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
