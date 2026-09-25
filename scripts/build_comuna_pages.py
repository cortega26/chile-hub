"""Genera páginas estáticas por comuna (SEO programático) desde el perfil territorial.

Una página única por comuna (`/comunas/{slug}/`) con indicadores consolidados
del perfil territorial + pobreza SAE, más un índice por región y un sitemap.
El contenido sale siempre de los Parquet normalizados: no hay cifras
hardcodeadas ni red. Se genera en el deploy de Pages (igual que `reference/`),
no se commitea.

Uso:
  python scripts/build_comuna_pages.py --out-dir comunas \
      --site-url https://tooltician.com/chile-hub
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import sys
from pathlib import Path

import polars as pl

ROOT_DIR = Path(__file__).resolve().parents[1]
PERFIL_PATH = ROOT_DIR / "data" / "normalized" / "perfil_territorial_comunal.parquet"
POBREZA_PATH = ROOT_DIR / "data" / "normalized" / "pobreza_comunal.parquet"
PUBLIC_SITE_URL = "https://tooltician.com/chile-hub/"
PARQUET_BASE = "https://tooltician.com/chile-hub/data/normalized"

REQUIRED_PERFIL_COLUMNS = {
    "codigo_region",
    "nombre_region",
    "codigo_comuna",
    "nombre_comuna",
    "nombre_comuna_clean",
    "poblacion_censada",
    "establecimientos_salud_total",
    "establecimientos_educacionales_total",
}

# Métricas que se muestran, en orden, agrupadas por bloque editorial.
IDENTIDAD = [
    ("Código CUT", "codigo_comuna"),
    ("Región", "nombre_region"),
    ("Provincia", "nombre_provincia"),
    ("Distrito electoral", "distrito_electoral"),
    ("Circunscripción senatorial", "circunscripcion_senatorial"),
    ("Población estimada", "poblacion_estimada"),
]
DEMOGRAFIA = [
    ("Población censada (2024)", "poblacion_censada"),
    ("Hombres", "poblacion_hombres"),
    ("Mujeres", "poblacion_mujeres"),
    ("0 a 14 años", "poblacion_0_14"),
    ("15 a 29 años", "poblacion_15_29"),
    ("30 a 44 años", "poblacion_30_44"),
    ("45 a 64 años", "poblacion_45_64"),
    ("65 años o más", "poblacion_65_mas"),
]
HOGARES = [
    ("Viviendas censadas", "viviendas_censadas"),
    ("Hogares censados", "hogares_censados"),
    ("Personas por hogar (promedio)", "promedio_personas_por_hogar"),
]
SERVICIOS = [
    ("Establecimientos de salud", "establecimientos_salud_total"),
    ("Establecimientos educacionales", "establecimientos_educacionales_total"),
    ("Matrícula total", "matricula_total"),
    ("Asistencia promedio", "asistencia_promedio"),
    ("Tasa de aprobación", "tasa_aprobacion"),
    ("Tasa de reprobación", "tasa_reprobacion"),
    ("Tasa de retiro", "tasa_retiro"),
]
MUNICIPIO = [
    ("Año de finanzas", "anio_finanzas"),
    ("Ingresos totales", "ingresos_totales"),
    ("Gastos totales", "gastos_totales"),
    ("Ingresos propios permanentes", "ingresos_propios_permanentes"),
    ("Fondo común municipal", "fondo_comun_municipal"),
    ("Gasto en personal", "gasto_personal"),
    ("Gasto en inversión", "gasto_inversion"),
]
TERRITORIO = [
    ("Indicadores urbanos SIEDU", "indicadores_siedu_total"),
    ("Crecimiento natural (último año)", "crecimiento_natural_ultimo_anio"),
    ("Viviendas autorizadas (último año)", "viviendas_autorizadas_ultimo_anio"),
    ("Superficie autorizada m² (último año)", "superficie_autorizada_m2_ultimo_anio"),
    ("MP2,5 promedio (último año)", "mp25_promedio_ultimo_anio"),
]

MONEY_FIELDS = {
    "ingresos_totales",
    "gastos_totales",
    "ingresos_propios_permanentes",
    "fondo_comun_municipal",
    "gasto_personal",
    "gasto_inversion",
}
FLOAT_FIELDS = {"promedio_personas_por_hogar", "mp25_promedio_ultimo_anio", "valor_promedio_siedu"}
PERCENT_FIELDS = {"asistencia_promedio", "tasa_aprobacion", "tasa_reprobacion", "tasa_retiro"}

PAGE_CSS = """
:root { --bg:#f7f6f0; --ink:#1a221f; --muted:#5b6b64; --brand:#123d30; --line:#dcd9cc; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font-family: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif; line-height:1.55; }
main { max-width: 900px; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
a { color: var(--brand); }
.crumbs { font-size:.85rem; color:var(--muted); margin-bottom:1rem; }
h1 { font-size:1.9rem; margin:0 0 .25rem; }
.sub { color:var(--muted); margin:0 0 1.5rem; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:1rem; }
.card { background:#fff; border:1px solid var(--line); border-radius:12px; padding:1rem 1.1rem; }
.card h2 { font-size:1rem; margin:0 0 .6rem; color:var(--brand); }
table { width:100%; border-collapse:collapse; font-size:.92rem; }
td { padding:.25rem 0; vertical-align:top; }
td:last-child { text-align:right; font-variant-numeric:tabular-nums; }
.actions { margin:1.5rem 0; display:flex; flex-wrap:wrap; gap:.6rem; }
.actions a { background:var(--brand); color:#fff; text-decoration:none; padding:.5rem .9rem;
  border-radius:8px; font-size:.9rem; }
footer { border-top:1px solid var(--line); margin-top:2.5rem; padding-top:1rem;
  color:var(--muted); font-size:.82rem; }
.list { columns:2; column-gap:2rem; font-size:.92rem; }
@media (max-width:640px){ .list{columns:1;} }
"""


def comuna_slug(row: dict) -> str:
    """Slug base de una comuna desde `nombre_comuna_clean` (sin tildes/ñ)."""
    clean = str(row.get("nombre_comuna_clean") or row.get("nombre_comuna") or "").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    if not slug:
        raise ValueError(f"comuna sin slug válido: {row!r}")
    return slug


def assign_slugs(rows: list[dict]) -> dict[str, str]:
    """Mapea `codigo_comuna` → slug, resolviendo colisiones con el CUT.

    Hoy las 346 comunas tienen `nombre_comuna_clean` único, pero si dos
    colisionan el slug lleva sufijo `-{codigo_comuna}` en ambas (determinista,
    sin depender del orden).
    """
    base_counts: dict[str, int] = {}
    for row in rows:
        slug = comuna_slug(row)
        base_counts[slug] = base_counts.get(slug, 0) + 1
    slugs: dict[str, str] = {}
    for row in rows:
        cut = str(row["codigo_comuna"])
        slug = comuna_slug(row)
        if base_counts[slug] > 1:
            slug = f"{slug}-{cut}"
        slugs[cut] = slug
    if len(set(slugs.values())) != len(slugs):
        raise SystemExit("ERROR: slugs de comuna duplicados tras resolver colisiones.")
    return slugs


def _fmt(value, field: str | None = None) -> str:
    if value is None:
        return "s/d"
    if isinstance(value, str):
        return html.escape(value)
    if isinstance(value, bool):
        return "sí" if value else "no"
    if isinstance(value, float):
        if field in PERCENT_FIELDS:
            return f"{value:.1f}%"
        if field in FLOAT_FIELDS:
            return f"{value:,.2f}".replace(",", ".")
        value = round(value)
    number = f"{int(value):,}".replace(",", ".")
    return f"${number}" if field in MONEY_FIELDS else number


def _table(title: str, pairs: list[tuple[str, str]]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(label)}</td><td>{value}</td></tr>" for label, value in pairs
    )
    return f'<section class="card"><h2>{html.escape(title)}</h2><table>{rows}</table></section>'


def _pairs(row: dict, spec: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [(label, _fmt(row.get(field), field)) for label, field in spec if field in row]


def _dataset_json_ld(row: dict, page_url: str, site_url: str) -> dict:
    nombre = row["nombre_comuna"]
    return {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": f"Perfil territorial de {nombre}",
        "description": (
            f"Indicadores consolidados de la comuna de {nombre} (población, "
            "vivienda, pobreza, salud, educación, finanzas municipales y "
            "territorio) a partir de fuentes oficiales de Chile."
        ),
        "url": page_url,
        "creator": {"@type": "Organization", "name": "chile-hub"},
        "isPartOf": {"@type": "DataCatalog", "name": "chile-hub", "url": site_url},
        "spatialCoverage": {
            "@type": "AdministrativeArea",
            "name": nombre,
            "containedInPlace": {"@type": "Country", "name": "Chile"},
        },
        "inLanguage": "es",
        "license": "https://github.com/cortega26/chile-hub/blob/main/DATA_LICENSES.md",
    }


def _json_for_html(obj: dict) -> str:
    """JSON listo para embeber en `<script>`: sin `<`/`>`/`&` crudos.

    Un nombre con `</script>` rompería el documento si se serializa tal cual;
    los escapes unicode mantienen el JSON válido y el HTML seguro.
    """
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_comuna_page(
    row: dict, poverty: dict, slug: str, site_url: str, generated_at: str
) -> str:
    """HTML completo de una comuna. Todos los textos se escapan."""
    nombre = str(row["nombre_comuna"])
    page_url = f"{site_url.rstrip('/')}/comunas/{slug}/"
    title = f"Comuna de {nombre}: población, pobreza y datos oficiales"
    description = (
        f"Indicadores oficiales de {nombre} ({row['nombre_region']}): población "
        f"censada, pobreza, vivienda, salud, educación y finanzas municipales. "
        "Datos curados por chile-hub."
    )
    poverty_pairs = []
    if poverty.get("ingresos") is not None:
        poverty_pairs.append(("Pobreza por ingresos (SAE 2022)", f"{poverty['ingresos']:.1f}%"))
    if poverty.get("multidimensional") is not None:
        poverty_pairs.append(
            ("Pobreza multidimensional (SAE 2022)", f"{poverty['multidimensional']:.1f}%")
        )
    if not poverty_pairs:
        poverty_pairs.append(("Pobreza comunal (SAE)", "s/d"))

    dataset_ld = _json_for_html(_dataset_json_ld(row, page_url, site_url))
    breadcrumb_ld = _json_for_html(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "chile-hub", "item": site_url},
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Comunas",
                    "item": f"{site_url.rstrip('/')}/comunas/",
                },
                {"@type": "ListItem", "position": 3, "name": nombre, "item": page_url},
            ],
        }
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} | chile-hub</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{page_url}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{page_url}">
<style>{PAGE_CSS}</style>
<script type="application/ld+json">
{dataset_ld}
</script>
<script type="application/ld+json">
{breadcrumb_ld}
</script>
</head>
<body>
<main>
<nav class="crumbs"><a href="{site_url.rstrip("/")}/">chile-hub</a> › <a href="{site_url.rstrip("/")}/comunas/">Comunas</a> › {html.escape(nombre)}</nav>
<h1>{html.escape(nombre)}</h1>
<p class="sub">Región de {html.escape(str(row["nombre_region"]))} · Provincia de {html.escape(str(row.get("nombre_provincia", "s/d")))}</p>
<div class="grid">
{_table("Identidad territorial", _pairs(row, IDENTIDAD))}
{_table("Demografía (Censo 2024)", _pairs(row, DEMOGRAFIA))}
{_table("Hogares y viviendas", _pairs(row, HOGARES))}
{_table("Pobreza", poverty_pairs)}
{_table("Servicios", _pairs(row, SERVICIOS))}
{_table("Finanzas municipales", _pairs(row, MUNICIPIO))}
{_table("Territorio y medio ambiente", _pairs(row, TERRITORIO))}
</div>
<div class="actions">
<a href="{PARQUET_BASE}/perfil_territorial_comunal.parquet">Descargar Parquet</a>
<a href="{PARQUET_BASE}/perfil_territorial_comunal.json">Descargar JSON</a>
<a href="{site_url.rstrip("/")}/reference/datasets/perfil_territorial_comunal/">Documentación de la capa</a>
</div>
<footer>
Fuente: datos oficiales de INE, BCN, MINSAL, MINEDUC, MDS, SINIM/SUBDERE y MMA,
curados y validados por <a href="{site_url.rstrip("/")}/">chile-hub</a>.
Atribución por capa en <a href="https://github.com/cortega26/chile-hub/blob/main/DATA_LICENSES.md">DATA_LICENSES.md</a>.
Generado el {generated_at}.
</footer>
</main>
</body>
</html>
"""


def render_index(rows: list[dict], slugs: dict[str, str], site_url: str) -> str:
    by_region: dict[str, list[dict]] = {}
    for row in rows:
        by_region.setdefault(str(row["nombre_region"]), []).append(row)
    sections = []
    for region in sorted(by_region):
        items = "".join(
            f'<li><a href="{slugs[str(r["codigo_comuna"])]}/">{html.escape(str(r["nombre_comuna"]))}</a></li>'
            for r in sorted(by_region[region], key=lambda r: str(r["nombre_comuna"]))
        )
        sections.append(
            f'<section class="card"><h2>{html.escape(region)}</h2><ul class="list">{items}</ul></section>'
        )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comunas de Chile: indicadores oficiales por comuna | chile-hub</title>
<meta name="description" content="Las 346 comunas de Chile con población censada, pobreza, vivienda, salud, educación y finanzas municipales. Datos oficiales curados por chile-hub.">
<link rel="canonical" href="{site_url.rstrip("/")}/comunas/">
<style>{PAGE_CSS}</style>
</head>
<body>
<main>
<nav class="crumbs"><a href="{site_url.rstrip("/")}/">chile-hub</a> › Comunas</nav>
<h1>Comunas de Chile</h1>
<p class="sub">Indicadores oficiales por comuna, generados desde el perfil territorial de chile-hub.</p>
<div class="grid">
{"".join(sections)}
</div>
<footer>Fuentes oficiales de Chile, curadas y validadas por <a href="{site_url.rstrip("/")}/">chile-hub</a>.</footer>
</main>
</body>
</html>
"""


def render_sitemap(urls: list[str], generated_at: str) -> str:
    entries = "".join(
        f"  <url><loc>{html.escape(url)}</loc><lastmod>{generated_at}</lastmod></url>\n"
        for url in urls
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}</urlset>\n"
    )


def load_rows(perfil_path: Path, pobreza_path: Path) -> tuple[list[dict], dict[str, dict]]:
    perfil = pl.read_parquet(perfil_path)
    missing = REQUIRED_PERFIL_COLUMNS - set(perfil.columns)
    if missing:
        raise SystemExit(f"ERROR: faltan columnas en {perfil_path}: {sorted(missing)}")
    if perfil["codigo_comuna"].n_unique() != perfil.height:
        raise SystemExit("ERROR: codigo_comuna duplicado en el perfil territorial.")
    rows = list(perfil.iter_rows(named=True))

    poverty: dict[str, dict] = {}
    pob = pl.read_parquet(pobreza_path)
    for record in pob.iter_rows(named=True):
        cut = str(record["codigo_comuna"])
        poverty.setdefault(cut, {})[str(record["dimension"])] = record.get("tasa")
    return rows, poverty


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(ROOT_DIR / "comunas"))
    parser.add_argument("--site-url", default=PUBLIC_SITE_URL)
    parser.add_argument("--perfil", default=str(PERFIL_PATH))
    parser.add_argument("--pobreza", default=str(POBREZA_PATH))
    parser.add_argument(
        "--generated-at",
        default=datetime.datetime.now(datetime.UTC).date().isoformat(),
        help="Fecha ISO para lastmod/atribución (default: hoy UTC).",
    )
    args = parser.parse_args(argv)

    rows, poverty = load_rows(Path(args.perfil), Path(args.pobreza))
    slugs = assign_slugs(rows)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for row in rows:
        slug = slugs[str(row["codigo_comuna"])]
        page_dir = out_dir / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            render_comuna_page(
                row,
                poverty.get(str(row["codigo_comuna"]), {}),
                slug,
                args.site_url,
                args.generated_at,
            ),
            encoding="utf-8",
        )

    (out_dir / "index.html").write_text(render_index(rows, slugs, args.site_url), encoding="utf-8")
    urls = [f"{args.site_url.rstrip('/')}/comunas/"] + [
        f"{args.site_url.rstrip('/')}/comunas/{slugs[str(row['codigo_comuna'])]}/" for row in rows
    ]
    (out_dir / "sitemap.xml").write_text(render_sitemap(urls, args.generated_at), encoding="utf-8")

    print(f"{len(rows)} comunas + 1 índice + sitemap → {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
