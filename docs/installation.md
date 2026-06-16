# Installation

## PyPI

```bash
pip install chile-hub
```

```python
from chile_hub import ChileHub

hub = ChileHub()
comunas = hub.load_polars("comunas")
```

## Data Cache

The wheel does not include generated data files. On first use, `ChileHub()`
downloads the verified `chile-hub-publishable-bundle.zip` asset from GitHub
Releases, checks its SHA256 file, and extracts it into the user cache directory.

Use the CLI to manage the cache:

```bash
chile-hub cache status
chile-hub cache update
chile-hub cache clear
```

Set `CHILE_HUB_CACHE_DIR` to override the cache location.

## Offline And Local Artifacts

For offline use, populate the cache before disconnecting:

```bash
chile-hub cache update
```

To use artifacts built from a local checkout, pass the normalized directory:

```python
from chile_hub import ChileHub

hub = ChileHub(data_dir="data/normalized")
```

## Pinning

Pin the package version with pip:

```bash
pip install chile-hub==0.1.0
```

Pin data by selecting the matching release tag when updating the cache:

```bash
chile-hub cache update --data-version v0.1.0
```
