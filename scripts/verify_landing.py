import contextlib
import json
import socket
import threading
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BUNDLE_PATH = ROOT_DIR / "data" / "normalized" / "hub_bundle.json"


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
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def compute_runtime_freshness(dataset):
    refreshed_at = parse_iso_datetime(dataset.get("refreshed_at_utc"))
    max_age_hours = dataset.get("freshness", {}).get("max_age_hours")
    if refreshed_at is None or not isinstance(max_age_hours, (int, float)):
        return {"status": "unknown", "age_hours": None, "max_age_hours": max_age_hours}
    age_hours = max((datetime.now(timezone.utc) - refreshed_at).total_seconds() / 3600, 0)
    return {
        "status": "fresh" if age_hours <= max_age_hours else "stale",
        "age_hours": round(age_hours, 2),
        "max_age_hours": max_age_hours,
    }


def status_rank(status):
    return {"ok": 0, "warn": 1, "error": 2}.get(status, 1)


def compute_runtime_overall_status(build_status, runtime_freshness):
    statuses = [entry["status"] for entry in runtime_freshness.values()]
    runtime_freshness_status = "warn" if any(status in {"stale", "unknown"} for status in statuses) else "ok"
    return runtime_freshness_status if status_rank(runtime_freshness_status) > status_rank(build_status) else build_status


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def local_server():
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(  # noqa: E731
        *args,
        directory=str(ROOT_DIR),
        **kwargs,
    )
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
    except ImportError as exc:
        fail(
            "Playwright no está disponible en el entorno actual. "
            "Instala dependencias con `make bootstrap` o `pip install -r requirements.txt`."
        )

    bundle = json.loads(BUNDLE_PATH.read_text(encoding="utf-8"))
    health = bundle.get("health", {})
    datasets = bundle.get("datasets", [])
    runtime_freshness = {dataset["dataset"]: compute_runtime_freshness(dataset) for dataset in datasets}
    live_count = health.get("live_count", 0)
    stale_count = sum(1 for freshness in runtime_freshness.values() if freshness["status"] == "stale")
    unknown_freshness_count = sum(
        1 for freshness in runtime_freshness.values() if freshness["status"] == "unknown"
    )
    degraded_count = health.get("degraded_count", 0)
    partial_coverage_count = health.get("partial_coverage_count", 0)
    drifted_count = health.get("drifted_count", 0)
    review_terms_count = health.get("review_terms_count", 0)
    warning_count = health.get("warning_count", 0)
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
    expected_status_subtitle = (
        f"{live_count}/{len(datasets)} capas operativas en modo live. "
        f"Estado build: {build_overall_status}. "
        f"Estado actual: {current_overall_status}. "
        f"{'Sin capas stale.' if stale_count == 0 else f'{stale_count} capas stale.'} "
        f"{'Sin capas con freshness unknown.' if unknown_freshness_count == 0 else f'{unknown_freshness_count} capas con freshness unknown.'} "
        f"{'Sin capas con drift.' if drifted_count == 0 else f'{drifted_count} capas con drift.'} "
        f"{'Sin capas degradadas.' if degraded_count == 0 else f'{degraded_count} capas degradadas.'} "
        f"{'Sin regresiones de cobertura.' if partial_coverage_count == 0 else f'{partial_coverage_count} capas con cobertura parcial.'} "
        f"{'Sin capas en review_terms.' if review_terms_count == 0 else f'{review_terms_count} capas en review_terms.'} "
        f"{'Sin warnings activos.' if warning_count == 0 else f'{warning_count} warnings activos.'}"
    )

    with local_server() as url, sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1600})
        page.goto(url, wait_until="networkidle")

        repo_href = page.locator("header a.btn.btn-secondary").get_attribute("href")
        if repo_href != "https://github.com/cortega26/chile-hub":
            fail(f"Unexpected repo href: {repo_href}")

        status_actions = page.locator("#status-actions .dataset-action").all_inner_texts()
        expected_status_actions = ["Status", "Health JSON", "Health MD", "Bundle JSON", "Reuse JSON", "Reuse MD", "Provenance JSON", "Provenance MD", "Drift JSON", "Drift MD", "Overview JSON", "Overview MD", "Catalog JSON", "Catalog MD", "Manifest"]
        if status_actions != expected_status_actions:
            fail(f"Unexpected status actions: {status_actions}")

        status_subtitle = page.locator("#status-subtitle").inner_text()
        if status_subtitle != expected_status_subtitle:
            fail(f"Unexpected status subtitle: {status_subtitle}")

        status_pills = page.locator("#status-pills .status-pill").all_inner_texts()
        if f"Estado build: {build_overall_status}" not in status_pills:
            fail(f"Build status pill not found: {status_pills}")
        if f"Estado actual: {current_overall_status}" not in status_pills:
            fail(f"Current status pill not found: {status_pills}")
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

        package_actions = page.locator("#package-actions .dataset-action").all_inner_texts()
        if len(package_actions) != 4 or not package_actions[0].startswith("Bundle ZIP · ") or package_actions[1:] != ["SHA256", "Bundle JSON", "Manifest"]:
            fail(f"Unexpected package actions: {package_actions}")

        package_meta = page.locator("#package-meta").inner_text()
        if "Tamaño:" not in package_meta or "sha256:" not in package_meta or "generado junto al último build" not in package_meta:
            fail(f"Unexpected package meta: {package_meta}")

        package_verify_title = page.locator(".package-verify-title").inner_text()
        if package_verify_title != "VERIFICAR INTEGRIDAD":
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
        if quickstart_titles != ["Python + helper", "DuckDB directo", "CLI y refresh local"]:
            fail(f"Unexpected quickstart titles: {quickstart_titles}")

        first_card = page.locator(".dataset-card").first
        first_card_name = first_card.locator(".dataset-name").inner_text()
        if first_card_name != "regiones":
            fail(f"Unexpected first dataset card: {first_card_name}")

        first_card_actions = first_card.locator(".dataset-action").all_inner_texts()
        if len(first_card_actions) < 4 or first_card_actions[0:2] != ["Docs", "Fuente"] or not first_card_actions[2].startswith("PARQUET · ") or not first_card_actions[3].startswith("JSON · "):
            fail(f"Unexpected first dataset actions: {first_card_actions}")

        artifact_meta = first_card.locator(".dataset-artifact-meta").all_inner_texts()
        if len(artifact_meta) < 2 or not artifact_meta[0].startswith("tipo: parquet · sha256: ") or not artifact_meta[1].startswith("tipo: json · sha256: "):
            fail(f"Unexpected artifact metadata: {artifact_meta}")

        first_card_facts = first_card.locator(".dataset-fact").all_inner_texts()
        expected_first_runtime_status = runtime_freshness["regiones"]["status"]
        if f"FRESHNESS\n{expected_first_runtime_status} ·" not in "\n".join(first_card_facts):
            fail(f"Freshness fact not found in first dataset card: {first_card_facts}")
        if "COVERAGE\n" not in "\n".join(first_card_facts):
            fail(f"Coverage fact not found in first dataset card: {first_card_facts}")
        if "DRIFT\n" not in "\n".join(first_card_facts):
            fail(f"Drift fact not found in first dataset card: {first_card_facts}")
        if "REUSO\nopen-attribution · CC BY" not in "\n".join(first_card_facts):
            fail(f"Reuse fact not found in first dataset card: {first_card_facts}")
        if "DEGRADACIÓN\n" not in "\n".join(first_card_facts):
            fail(f"Degradation fact not found in first dataset card: {first_card_facts}")

        first_card_meta = first_card.locator(".dataset-meta-line").first.inner_text()
        if "Requiere atribución: sí" not in first_card_meta:
            fail(f"Reuse attribution metadata not found in first dataset card: {first_card_meta}")
        freshness_meta = first_card.locator(".dataset-meta-line").nth(1).inner_text()
        if "Freshness build:" not in freshness_meta or "Freshness actual:" not in freshness_meta:
            fail(f"Runtime freshness metadata not found in first dataset card: {freshness_meta}")

        example_title = first_card.locator(".dataset-example-title").inner_text()
        if example_title.upper() != "RECETA DE USO":
            fail(f"Unexpected dataset example title: {example_title}")

        initial_line = first_card.locator(".dataset-example-code").inner_text().splitlines()[0]
        if initial_line != "from src.chile_hub import ChileHub":
            fail(f"Unexpected initial example line: {initial_line}")

        first_card.locator(".dataset-example-tab", has_text="duckdb").click()
        page.wait_for_timeout(100)
        after_tab_line = first_card.locator(".dataset-example-code").inner_text().splitlines()[0]
        if after_tab_line != "SELECT *":
            fail(f"Unexpected duckdb example line: {after_tab_line}")

        first_card.locator(".dataset-example-tab", has_text="cli").click()
        page.wait_for_timeout(100)
        copy_button = first_card.locator(".dataset-example-copy")
        copy_button.click()
        page.wait_for_timeout(150)
        if copy_button.inner_text() != "Copiado":
            fail(f"Dataset example copy button did not change label: {copy_button.inner_text()}")
        copied_class = copy_button.evaluate("el => el.classList.contains('copied')")
        if not copied_class:
            fail("Dataset example copy button did not activate copied class")

        browser.close()

    print(
        "Landing verification passed: status, package surface, freshness, coverage, drift, reuse metadata, "
        "quickstart, artifact metadata, dataset examples and copy interactions are working."
    )


if __name__ == "__main__":
    verify_landing()
