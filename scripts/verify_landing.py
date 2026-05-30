import contextlib
import socket
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def fail(message):
    print(f"ERROR: {message}")
    raise SystemExit(1)


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

    with local_server() as url, sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1600})
        page.goto(url, wait_until="networkidle")

        repo_href = page.locator("header a.btn.btn-secondary").get_attribute("href")
        if repo_href != "https://github.com/cortega26/chile-hub":
            fail(f"Unexpected repo href: {repo_href}")

        status_actions = page.locator("#status-actions .dataset-action").all_inner_texts()
        expected_status_actions = ["Status", "Catalog JSON", "Catalog MD", "Manifest"]
        if status_actions != expected_status_actions:
            fail(f"Unexpected status actions: {status_actions}")

        quickstart_titles = page.locator(".quickstart-title").all_inner_texts()
        if quickstart_titles != ["Python + helper", "DuckDB directo", "CLI y refresh local"]:
            fail(f"Unexpected quickstart titles: {quickstart_titles}")

        first_card = page.locator(".dataset-card").first
        first_card_name = first_card.locator(".dataset-name").inner_text()
        if first_card_name != "regiones":
            fail(f"Unexpected first dataset card: {first_card_name}")

        first_card_actions = first_card.locator(".dataset-action").all_inner_texts()
        if first_card_actions[:4] != ["Docs", "Fuente", "PARQUET · 1.3 KB", "JSON · 1.3 KB"]:
            fail(f"Unexpected first dataset actions: {first_card_actions}")

        artifact_meta = first_card.locator(".dataset-artifact-meta").all_inner_texts()
        expected_artifact_meta = [
            "tipo: parquet · sha256: ac709667dc44",
            "tipo: json · sha256: d7f3b237f532",
        ]
        if artifact_meta[:2] != expected_artifact_meta:
            fail(f"Unexpected artifact metadata: {artifact_meta}")

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
        "Landing verification passed: status, quickstart, artifact metadata, "
        "dataset examples and copy interactions are working."
    )


if __name__ == "__main__":
    verify_landing()
