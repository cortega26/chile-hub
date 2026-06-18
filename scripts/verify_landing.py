import contextlib
import json
import socket
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import tomllib

ROOT_DIR = Path(__file__).resolve().parents[1]
UTC = timezone.utc
BUNDLE_PATH = ROOT_DIR / "data" / "normalized" / "hub_bundle.json"
PRODUCTION_CSP = (
    "default-src 'self'; base-uri 'self'; form-action 'self' https://formspree.io; "
    "frame-ancestors 'none'; object-src 'none'; "
    "script-src 'self' https://analytics.ahrefs.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; "
    "connect-src 'self' https://analytics.ahrefs.com https://formspree.io; "
    "manifest-src 'self'; media-src 'self'; worker-src 'self' blob:; upgrade-insecure-requests"
)


def load_project_metadata():
    with open(ROOT_DIR / "pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
    public_site_url = (
        pyproject_data.get("tool", {})
        .get("chile_hub", {})
        .get("public_site_url", "https://tooltician.com/chile-hub/")
    )
    return pyproject_data.get("project", {}), public_site_url.rstrip("/") + "/"


class LandingRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Content-Security-Policy", PRODUCTION_CSP)
        super().end_headers()


def fail(message):
    print(f"ERROR: {message}")
    raise SystemExit(1)


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def compute_runtime_freshness(dataset):
    refreshed_at = parse_iso_datetime(dataset.get("refreshed_at_utc"))
    max_age_hours = dataset.get("freshness", {}).get("max_age_hours")
    if refreshed_at is None or not isinstance(max_age_hours, (int, float)):
        return {"status": "unknown", "age_hours": None, "max_age_hours": max_age_hours}
    age_hours = max((datetime.now(UTC) - refreshed_at).total_seconds() / 3600, 0)
    return {
        "status": "fresh" if age_hours <= max_age_hours else "stale",
        "age_hours": round(age_hours, 2),
        "max_age_hours": max_age_hours,
    }


def status_rank(status):
    return {"ok": 0, "warn": 1, "error": 2}.get(status, 1)


def compute_runtime_overall_status(build_status, runtime_freshness):
    statuses = [entry["status"] for entry in runtime_freshness.values()]
    runtime_freshness_status = (
        "warn" if any(status in {"stale", "unknown"} for status in statuses) else "ok"
    )
    return (
        runtime_freshness_status
        if status_rank(runtime_freshness_status) > status_rank(build_status)
        else build_status
    )


def verify_local_site_asset(url_value, public_site_url, label):
    if not url_value:
        fail(f"Missing {label}")
    parsed_public = urlparse(public_site_url)
    parsed_url = urlparse(url_value)
    if parsed_url.scheme not in {"http", "https"}:
        fail(f"{label} must be an absolute URL: {url_value}")
    if parsed_url.netloc != parsed_public.netloc:
        return
    public_path = parsed_public.path.rstrip("/") + "/"
    if not parsed_url.path.startswith(public_path):
        fail(f"{label} is outside public site path: {url_value}")
    relative_path = parsed_url.path.removeprefix(public_path)
    asset_path = ROOT_DIR / relative_path
    if not asset_path.is_file():
        fail(f"{label} points to missing local asset: {relative_path}")


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def local_server():
    def handler(*args, **kwargs):
        return LandingRequestHandler(*args, directory=str(ROOT_DIR), **kwargs)

    port = get_free_port()
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def verify_landing():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail(
            "Playwright no está disponible en el entorno actual. "
            "Instala dependencias con `make bootstrap` o `pip install -r requirements.txt`."
        )

    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    health = bundle.get("health", {})
    datasets = bundle.get("datasets", [])
    datasets_by_name = {dataset.get("dataset"): dataset for dataset in datasets}
    top_issue = health.get("top_issue") or bundle.get("top_issue") or {}
    top_issue_dataset = top_issue.get("dataset")
    top_issue_source_detail = top_issue.get("source_detail") or datasets_by_name.get(
        top_issue_dataset, {}
    ).get("source_detail")
    runtime_freshness = {
        dataset["dataset"]: compute_runtime_freshness(dataset) for dataset in datasets
    }

    unknown_freshness_count = sum(
        1 for freshness in runtime_freshness.values() if freshness["status"] == "unknown"
    )
    degraded_count = health.get("degraded_count", 0)
    partial_coverage_count = health.get("partial_coverage_count", 0)
    drifted_count = health.get("drifted_count", 0)
    review_terms_count = health.get("review_terms_count", 0)
    top_issue_warning_count = datasets_by_name.get(top_issue_dataset, {}).get("warning_count", 0)
    top_issue_reason = top_issue.get("diagnostic_summary")
    top_issue_action = top_issue.get("recommended_action")
    build_overall_status = bundle.get("overall_status", "unknown")
    current_overall_status = compute_runtime_overall_status(build_overall_status, runtime_freshness)
    zip_package = next(
        (package for package in bundle.get("packages", []) if package.get("package_type") == "zip"),
        None,
    )
    expected_verification_command = (
        zip_package.get("verification_command")
        if zip_package and zip_package.get("verification_command")
        else "shasum -a 256 -c data/normalized/chile-hub-publishable-bundle.zip.sha256"
    )

    with local_server() as url, sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1600})
        browser_errors = []
        page.on(
            "console",
            lambda message: (
                browser_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.on("pageerror", lambda error: browser_errors.append(str(error)))
        page.goto(url, wait_until="networkidle")

        if browser_errors:
            fail(f"Browser errors while rendering landing: {browser_errors}")

        # Version and public URL verification.
        # La versión se lee de hub_bundle.json (fuente única de verdad) y app.js
        # la inyecta dinámicamente en el badge. Así no hay riesgo de desincronización
        # entre pyproject.toml e index.html.
        project_metadata, public_site_url = load_project_metadata()
        public_data_base = public_site_url + "data/normalized"
        expected_version = bundle.get("version")
        if not expected_version:
            fail("hub_bundle.json is missing version field")
        navbar_badge = page.locator(".badge-alpha")
        if navbar_badge.count() != 1:
            fail("Expected exactly one .badge-alpha version badge in the navbar")
        # Espera a que app.js haya poblado el badge desde hub_bundle.json.
        try:
            page.wait_for_function(
                "document.querySelector('.badge-alpha')?.textContent?.startsWith('v')",
                timeout=5000,
            )
        except Exception:
            fail("Version badge was not populated by app.js within 5 seconds")
        navbar_badge_text = navbar_badge.inner_text()
        if navbar_badge_text != f"v{expected_version}":
            fail(
                f"Version badge mismatch: expected 'v{expected_version}', got '{navbar_badge_text}'"
            )

        # SEO Verification
        canonical = page.locator("link[rel='canonical']").get_attribute("href")
        if canonical != public_site_url:
            fail(f"Unexpected canonical link: {canonical}")

        description = page.locator("meta[name='description']").get_attribute("content")
        if not description or "chile-hub" not in description:
            fail(f"Unexpected or missing description: {description}")

        robots = page.locator("meta[name='robots']").get_attribute("content")
        if robots != "index, follow":
            fail(f"Unexpected robots meta: {robots}")

        og_title = page.locator("meta[property='og:title']").get_attribute("content")
        if og_title != "chile-hub — Capas de Datos de Chile":
            fail(f"Unexpected og:title: {og_title}")

        og_image = page.locator("meta[property='og:image']").get_attribute("content")
        verify_local_site_asset(og_image, public_site_url, "og:image")

        twitter_card = page.locator("meta[name='twitter:card']").get_attribute("content")
        if twitter_card != "summary_large_image":
            fail(f"Unexpected twitter:card: {twitter_card}")

        twitter_image = page.locator("meta[name='twitter:image']").get_attribute("content")
        verify_local_site_asset(twitter_image, public_site_url, "twitter:image")

        json_ld_count = page.locator("script[type='application/ld+json']").count()
        if json_ld_count < 2:
            fail(f"Expected at least 2 JSON-LD script tags, found {json_ld_count}")

        # Accessibility (a11y) Verification
        skip_link = page.locator("a.skip-link")
        if skip_link.count() != 1:
            fail("Expected exactly one skip link element")
        if skip_link.get_attribute("href") != "#main-content":
            fail(f"Unexpected skip link href: {skip_link.get_attribute('href')}")

        main_content = page.locator("main#main-content")
        if main_content.count() != 1:
            fail("Expected exactly one main element with id='main-content'")

        catalog_label = page.locator("#catalog-search-input").get_attribute("aria-label")
        if catalog_label != "Filtrar catálogo de capas":
            fail(f"Unexpected or missing aria-label for #catalog-search-input: {catalog_label}")

        search_label = page.locator("#search-input").get_attribute("aria-label")
        if search_label != "Buscar comuna, provincia o región":
            fail(f"Unexpected or missing aria-label for #search-input: {search_label}")

        region_label = page.locator("#region-filter").get_attribute("aria-label")
        if region_label != "Filtrar comunas por región":
            fail(f"Unexpected or missing aria-label for #region-filter: {region_label}")

        repo_href = page.get_by_role("link", name="GitHub Repo").get_attribute("href")
        if repo_href != "https://github.com/cortega26/chile-hub":
            fail(f"Unexpected repo href: {repo_href}")

        page.locator(".technical-details").click()
        status_actions = page.locator("#status-actions .dataset-action").all_inner_texts()
        expected_status_actions = [
            "Status",
            "Status JSON",
            "Health JSON",
            "Health MD",
            "Bundle JSON",
            "Reuse JSON",
            "Reuse MD",
            "Provenance JSON",
            "Provenance MD",
            "Drift JSON",
            "Drift MD",
            "Overview JSON",
            "Overview MD",
            "Catalog JSON",
            "Catalog MD",
            "Manifest",
            "Ver top issue",
        ]
        if status_actions != expected_status_actions:
            fail(f"Unexpected status actions: {status_actions}")
        top_issue_href = page.get_by_role("link", name="Ver top issue").get_attribute("href")
        if top_issue_href != f"#dataset-{top_issue_dataset}":
            fail(f"Unexpected top issue href: {top_issue_href}")

        status_subtitle = page.locator("#status-subtitle").inner_text()
        expected_substring = f"{len(datasets)} capas disponibles. Último build:"
        if expected_substring not in status_subtitle:
            fail(f"Unexpected status subtitle: {status_subtitle}")
        status_meta_locator = page.locator("#status-meta")
        if status_meta_locator.count() != 1:
            fail("Expected exactly one #status-meta element")
        status_meta = status_meta_locator.inner_text()
        if top_issue_dataset:
            parts = [f"{top_issue_dataset}: {top_issue_reason}"]
            if top_issue_action:
                parts.append(top_issue_action)
            if top_issue_source_detail and top_issue_source_detail != "unknown":
                parts.append(f"Fuente: {top_issue_source_detail}")
            expected_status_meta = " · ".join(parts)
        else:
            expected_status_meta = ""
        if status_meta != expected_status_meta:
            fail(f"Unexpected status meta: {status_meta}")

        status_pills = page.locator("#status-pills .status-pill").all_inner_texts()
        if f"Estado build: {build_overall_status}" not in status_pills:
            fail(f"Build status pill not found: {status_pills}")
        if f"Estado actual: {current_overall_status}" not in status_pills:
            fail(f"Current status pill not found: {status_pills}")
        if f"Top issue: {top_issue_dataset}" not in status_pills:
            fail(f"Top issue pill not found: {status_pills}")
        if f"Review terms: {review_terms_count}" not in status_pills:
            fail(f"Review terms pill not found: {status_pills}")
        if f"Degraded: {degraded_count}" not in status_pills:
            fail(f"Degraded pill not found: {status_pills}")
        if f"Drifted: {drifted_count}" not in status_pills:
            fail(f"Drifted pill not found: {status_pills}")
        if f"Freshness unknown: {unknown_freshness_count}" not in status_pills:
            fail(f"Freshness unknown pill not found: {status_pills}")
        if f"Partial coverage: {partial_coverage_count}" not in status_pills:
            fail(f"Partial coverage pill not found: {status_pills}")

        package_actions = [
            action.strip()
            for action in page.locator("#package-actions .dataset-action").all_inner_texts()
        ]
        if (
            len(package_actions) != 4
            or not package_actions[0].startswith("Bundle ZIP · ")
            or package_actions[1:] != ["SHA256", "Bundle JSON", "Manifest"]
        ):
            fail(f"Unexpected package actions: {package_actions}")

        package_meta = page.locator("#package-meta").inner_text()
        if (
            "Tamaño:" not in package_meta
            or "sha256:" not in package_meta
            or "generado junto al último build" not in package_meta
        ):
            fail(f"Unexpected package meta: {package_meta}")

        page.locator(".package-verify summary").click()
        package_verify_title = page.locator(".package-verify-title").inner_text()
        if package_verify_title != "Verificar integridad":
            fail(f"Unexpected package verify title: {package_verify_title}")

        package_verify_line = page.locator("#package-verify-code").inner_text().splitlines()[0]
        if package_verify_line != expected_verification_command:
            fail(f"Unexpected package verify command: {package_verify_line}")

        package_copy = page.locator("#package-verify-copy")
        package_copy.click()
        page.wait_for_timeout(150)
        if package_copy.inner_text() != "Copiado":
            fail(f"Package verify copy button did not change label: {package_copy.inner_text()}")

        quickstart_titles = page.locator(".quickstart-title").all_inner_texts()
        if quickstart_titles != [
            "Python + Polars",
            "DuckDB directo",
            "JSON + curl",
        ]:
            fail(f"Unexpected quickstart titles: {quickstart_titles}")

        quickstart_code = page.locator("#quickstart-python").inner_text()
        if f"{public_data_base}/comunas.parquet" not in quickstart_code:
            fail(f"Public data URL missing from quickstart: {quickstart_code}")

        first_card = page.locator(".dataset-card").first
        first_card_name = first_card.locator(".dataset-name").inner_text()
        if first_card_name != top_issue_dataset:
            fail(f"Unexpected first dataset card: {first_card_name}")

        first_card_actions = [
            t for t in first_card.locator(".dataset-action").all_inner_texts() if t
        ]
        # Algunos datasets (ej. empresas) no tienen JSON por tamaño →
        # no hay acción JSON ni botón "Vista previa" (app.js L571-572).
        _has_json = len(first_card_actions) >= 2 and first_card_actions[1].startswith("JSON · ")
        if not first_card_actions[0].startswith("PARQUET · "):
            fail(f"Unexpected first dataset action 0 (expected PARQUET): {first_card_actions}")
        if "Ficha técnica" not in first_card_actions:
            fail(f"Ficha técnica action not found: {first_card_actions}")

        _preview_btn = first_card.get_by_role("button", name="Vista previa")
        if _preview_btn.count() > 0:
            _preview_btn.click()
            preview_rows = first_card.locator(".dataset-preview-table tbody tr")
            preview_rows.first.wait_for()
            preview_row_count = preview_rows.count()
            if preview_row_count > 5:
                fail(f"Unexpected preview row count: {preview_row_count}")
            if first_card.locator(".dataset-preview-table th").count() == 0:
                fail("Dataset preview did not render column headers")

        first_card.locator(".dataset-details").click()

        artifact_meta = first_card.locator(".dataset-artifact-meta").all_inner_texts()
        if len(artifact_meta) < 1 or not artifact_meta[0].startswith("tipo: parquet · sha256: "):
            fail(f"Unexpected artifact metadata: {artifact_meta}")
        if _has_json:
            if len(artifact_meta) < 2 or not artifact_meta[1].startswith("tipo: json · sha256: "):
                fail(f"Missing JSON artifact metadata: {artifact_meta}")

        first_card_facts = first_card.locator(".dataset-fact").all_inner_texts()
        first_card_facts_text = "\n".join(first_card_facts).upper()
        expected_first_runtime_status = runtime_freshness[top_issue_dataset]["status"]
        if f"FRESHNESS\n{expected_first_runtime_status.upper()} ·" not in first_card_facts_text:
            fail(f"Freshness fact not found in first dataset card: {first_card_facts}")
        if "COVERAGE\n" not in first_card_facts_text:
            fail(f"Coverage fact not found in first dataset card: {first_card_facts}")
        if "DRIFT\n" not in first_card_facts_text:
            fail(f"Drift fact not found in first dataset card: {first_card_facts}")
        if "REUSO\n" not in first_card_facts_text:
            fail(f"Reuse fact not found in first dataset card: {first_card_facts}")
        if "DEGRADACIÓN\n" not in first_card_facts_text:
            fail(f"Degradation fact not found in first dataset card: {first_card_facts}")

        first_card_meta = first_card.locator(".dataset-meta-line").first.inner_text()
        if "Requiere atribución: sí" not in first_card_meta:
            fail(f"Reuse attribution metadata not found in first dataset card: {first_card_meta}")
        provenance_meta = first_card.locator(".dataset-meta-line").nth(1).inner_text()
        if (
            "Procedencia técnica:" not in provenance_meta
            or top_issue_source_detail not in provenance_meta
            or f"Warnings: {top_issue_warning_count}" not in provenance_meta
        ):
            fail(
                f"Technical provenance metadata not found in first dataset card: {provenance_meta}"
            )
        freshness_meta = first_card.locator(".dataset-meta-line").nth(2).inner_text()
        if "Freshness build:" not in freshness_meta or "Freshness actual:" not in freshness_meta:
            fail(f"Runtime freshness metadata not found in first dataset card: {freshness_meta}")

        example_title = first_card.locator(".dataset-example-title").inner_text()
        if example_title.upper() != "RECETA DE USO":
            fail(f"Unexpected dataset example title: {example_title}")

        initial_line = first_card.locator(".dataset-example-code").inner_text().splitlines()[0]
        if initial_line != "import polars as pl":
            fail(f"Unexpected initial example line: {initial_line}")

        if public_site_url not in first_card.locator(".dataset-example-code").inner_text():
            fail("Dataset recipe does not use a public URL")

        first_card.locator(".dataset-example-tab", has_text="duckdb").click()
        page.wait_for_timeout(100)
        after_tab_line = first_card.locator(".dataset-example-code").inner_text().splitlines()[0]
        if after_tab_line != "SELECT *":
            fail(f"Unexpected duckdb example line: {after_tab_line}")

        # Solo hace clic en curl si el dataset tiene salida JSON
        # (app.js buildDatasetExample solo renderiza el tab curl cuando jsonName existe).
        curl_tab = first_card.locator(".dataset-example-tab", has_text="curl")
        if curl_tab.count() > 0:
            curl_tab.click()
            page.wait_for_timeout(100)
        copy_button = first_card.locator(".dataset-example-copy")
        copy_button.click()
        page.wait_for_timeout(150)
        if copy_button.inner_text() != "Copiado":
            fail(f"Dataset example copy button did not change label: {copy_button.inner_text()}")
        copied_class = copy_button.evaluate("el => el.classList.contains('copied')")
        if not copied_class:
            fail("Dataset example copy button did not activate copied class")

        monedario_bridges = page.locator(".monedario-bridge")
        if monedario_bridges.count() != 1:
            fail(f"Expected one Monedario bridge, found {monedario_bridges.count()}")
        monedario_bridge = page.locator("#dataset-indicadores .monedario-bridge")
        if monedario_bridge.count() != 1:
            fail("Monedario bridge must belong to the indicadores card")
        monedario_copy = monedario_bridge.text_content() or ""
        if "Chile Hub publica los datos; Monedario explica" not in monedario_copy:
            fail(f"Unexpected Monedario bridge copy: {monedario_copy}")
        monedario_href = monedario_bridge.locator("a").get_attribute("href")
        if monedario_href != "https://monedario.cl/guias/uf-costo-de-vida/":
            fail(f"Unexpected Monedario href: {monedario_href}")

        request_dataset_href = page.get_by_role("link", name="Solicitar un dataset").get_attribute(
            "href"
        )
        if "github.com/cortega26/chile-hub/issues/new" not in request_dataset_href:
            fail(f"Unexpected dataset request href: {request_dataset_href}")
        share_project_href = page.get_by_role("link", name="Compartir un proyecto").get_attribute(
            "href"
        )
        if "github.com/cortega26/chile-hub/issues/new" not in share_project_href:
            fail(f"Unexpected project sharing href: {share_project_href}")

        top_issue_card = (
            page.locator(".dataset-card")
            .filter(has=page.locator(".dataset-name", has_text=top_issue_dataset))
            .first
        )
        page.get_by_role("link", name="Ver top issue").click()
        page.wait_for_timeout(100)
        hash_value = page.evaluate("() => window.location.hash")
        if hash_value != f"#dataset-{top_issue_dataset}":
            fail(f"Unexpected hash after top issue click: {hash_value}")
        top_issue_meta = top_issue_card.locator(".dataset-meta-line").all_inner_texts()
        if not any(f"Warnings: {top_issue_warning_count}" in line for line in top_issue_meta):
            fail(f"Warning count not found in top issue card metadata: {top_issue_meta}")
        if not any("Acción recomendada:" in line for line in top_issue_meta):
            fail(f"Recommended action not found in top issue card metadata: {top_issue_meta}")

        browser.close()

    print(
        "Landing verification passed: status, package surface, freshness, coverage, drift, reuse metadata, "
        "public quickstart, previews, feedback actions, artifact metadata, dataset examples and copy interactions are working."
    )


if __name__ == "__main__":
    verify_landing()
