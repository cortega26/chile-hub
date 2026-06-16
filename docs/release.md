# Release Process

`chile-hub` publishes software releases to PyPI and data refreshes as verified
normalized artifacts. These are related but intentionally separate flows.

## Versioning

Use Conventional Commits:

- `fix:` bumps PATCH.
- `feat:` bumps MINOR.
- `feat!:` or `BREAKING CHANGE:` bumps MAJOR.
- `docs:`, `test:`, `style:`, and data refresh commits do not publish by default.

The canonical software version is `project.version` in `pyproject.toml`.
`python-semantic-release` updates it, creates a Git tag, creates a GitHub
Release, builds the wheel and source distribution, and publishes through PyPI
Trusted Publishing.

## TestPyPI

Use the manual `TestPyPI Package Smoke` workflow before enabling a production
release for a major packaging change. It builds the package, publishes to
TestPyPI, installs the wheel in a clean environment, imports `chile_hub`, and
runs `chile-hub --help`.

## Production PyPI

The `PyPI Release` workflow runs on pushes to `main`. It skips `[skip ci]`
commits, computes the next version from Conventional Commits, publishes through
OIDC Trusted Publishing, and attaches the latest verified data bundle plus
metadata assets to the GitHub Release.

## Data-Only Refreshes

Scheduled data refreshes keep using the pipeline workflow. They validate live
data, update `data/normalized/`, and commit with:

```text
chore(data): daily refresh [skip ci]
```

Those commits do not create a new PyPI version.
