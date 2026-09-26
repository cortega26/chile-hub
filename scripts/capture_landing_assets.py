"""Captura los assets visuales del README desde la landing local.

Genera screenshots deterministas (`docs/assets/*.png`) y un clip WebP animado
del explorador SQL, sirviendo el repo con el mismo handler que usa
`scripts/verify_landing.py` (sin depender del sitio desplegado).

Uso:
  python scripts/capture_landing_assets.py            # todo
  python scripts/capture_landing_assets.py --skip-clip # solo screenshots

Requiere Playwright (ya es dependencia dev) y ffmpeg con libwebp_anim en el
PATH para el clip. Los assets se regeneran a mano cuando la landing cambie de
diseño; no corren en CI para no acoplar los tests a snapshots visuales.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT_DIR / "docs" / "assets"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from verify_landing import local_server  # noqa: E402


def _scroll_below_header(page, selector: str) -> None:
    """Deja la sección visible bajo el header sticky (que si no la tapa).

    Usa `behavior: "instant"` para vencer el `scroll-behavior: smooth` global:
    con smooth, un scrollIntoView seguido de scrollBy se cancela a sí mismo.
    """
    page.evaluate(
        "(sel) => { const el = document.querySelector(sel);"
        " const top = el.getBoundingClientRect().top + window.scrollY - 96;"
        " window.scrollTo({ top, behavior: 'instant' }); }",
        selector,
    )
    page.wait_for_timeout(200)


def capture_screenshots(assets_dir: Path) -> None:
    from playwright.sync_api import sync_playwright

    with local_server() as url, sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=2)
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector("#catalog-grid .dataset-card")

        page.screenshot(path=str(assets_dir / "landing-hero.png"))

        _scroll_below_header(page, "#catalogo")
        page.screenshot(path=str(assets_dir / "landing-catalogo.png"))

        _scroll_below_header(page, "#hub-health-section")
        page.screenshot(path=str(assets_dir / "landing-health.png"))

        _scroll_below_header(page, "#explorador")
        page.screenshot(path=str(assets_dir / "landing-sql.png"))

        mobile = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=3)
        mobile.goto(url, wait_until="networkidle")
        mobile.wait_for_selector("#catalog-grid .dataset-card")
        mobile.screenshot(path=str(assets_dir / "landing-mobile.png"))

        browser.close()


def capture_demo_clip(assets_dir: Path, tmp_dir: Path) -> Path:
    """Graba el explorador SQL y lo convierte a WebP animado.

    WebP animado en vez de GIF: misma demo con la mitad del peso (el repo
    rechaza archivos >500 KB vía check-added-large-files).
    """
    from playwright.sync_api import sync_playwright

    video_dir = tmp_dir / "video"
    video_dir.mkdir(parents=True, exist_ok=True)

    with local_server() as url, sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(video_dir),
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector("#catalog-grid .dataset-card")
        page.wait_for_timeout(800)

        page.locator("#explorador").scroll_into_view_if_needed()
        page.wait_for_timeout(600)
        page.fill(
            "#sql-input",
            "SELECT nombre_comuna, poblacion_censada FROM read_parquet('data/normalized/censo_comunal.parquet') ORDER BY poblacion_censada DESC LIMIT 5;",
        )
        page.click("#sql-run-btn")
        page.wait_for_selector("#sql-result table", timeout=30000)
        page.wait_for_timeout(2200)

        context.close()
        browser.close()

    videos = sorted(video_dir.glob("*.webm"))
    if not videos:
        raise SystemExit("ERROR: Playwright no generó video (.webm) para el clip")

    if not shutil.which("ffmpeg"):
        raise SystemExit("ERROR: ffmpeg no está en el PATH; usa --skip-clip")

    webp_path = assets_dir / "demo-sql.webp"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            "1.2",
            "-i",
            str(videos[0]),
            "-vcodec",
            "libwebp_anim",
            "-filter:v",
            "fps=8,scale=880:-1:flags=lanczos",
            "-lossless",
            "0",
            "-compression_level",
            "6",
            "-q:v",
            "62",
            "-loop",
            "0",
            "-an",
            "-vsync",
            "0",
            str(webp_path),
        ],
        check=True,
        capture_output=True,
    )
    return webp_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-clip", action="store_true", help="No genera el clip WebP de demo")
    args = parser.parse_args(argv)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    capture_screenshots(ASSETS_DIR)
    for name in (
        "landing-hero.png",
        "landing-catalogo.png",
        "landing-health.png",
        "landing-sql.png",
        "landing-mobile.png",
    ):
        size_kb = (ASSETS_DIR / name).stat().st_size // 1024
        print(f"assets: {name} ({size_kb} KB)")

    if not args.skip_clip:
        with tempfile.TemporaryDirectory(prefix="chile-hub-clip-") as tmp:
            clip_path = capture_demo_clip(ASSETS_DIR, Path(tmp))
        print(f"assets: {clip_path.name} ({clip_path.stat().st_size // 1024} KB)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
