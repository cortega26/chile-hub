"""Regression checks for the LinkedIn / Open Graph social preview.

The previous thumbnail was an unattractive screenshot-style card despite valid
og:image tags. Check the source artwork, cache busting, and Pages render step
together so future deployments cannot silently fall back to the old asset.
"""

from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
IMAGE_URL = "https://tooltician.com/chile-hub/social-card.png?v=2"


def test_social_preview_artwork_dimensions_and_copy():
    svg_path = ROOT / "social-card-source.svg"
    assert svg_path.is_file()
    tree = ElementTree.parse(svg_path)
    root = tree.getroot()
    assert root.attrib["width"] == "1200"
    assert root.attrib["height"] == "630"
    assert root.attrib["viewBox"] == "0 0 1200 630"
    texts = " ".join(element.text or "" for element in root.iter())
    assert "chile-hub" in texts
    assert "Capas de Datos de Chile" in texts
    assert "normalizados y validados" in texts


def test_social_preview_metadata_is_absolute_raster_and_cache_busted():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert f'<meta property="og:image" content="{IMAGE_URL}">' in html
    assert f'<meta property="og:image:secure_url" content="{IMAGE_URL}">' in html
    assert f'<meta name="twitter:image" content="{IMAGE_URL}">' in html
    assert '<meta property="og:image:type" content="image/png">' in html
    assert '<meta property="og:image:width" content="1200">' in html
    assert '<meta property="og:image:height" content="630">' in html
    assert '<meta property="og:image:alt"' in html
    assert '<meta name="twitter:image:alt"' in html


def test_pages_deploy_renders_png_before_uploading_artifact():
    workflow = (ROOT / ".github/workflows/pages-deploy.yml").read_text(
        encoding="utf-8"
    )
    render = workflow.index("Render social preview (1200x630 PNG)")
    conversion = workflow.index('cairosvg.svg2png(url="social-card-source.svg"')
    upload = workflow.index("- name: Upload Pages artifact")
    assert render < conversion < upload
    assert 'data.startswith(b"\\x89PNG\\r\\n\\x1a\\n")' in workflow
    assert "struct.unpack(\">II\", data[16:24]) == (1200, 630)" in workflow
