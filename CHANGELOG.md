# Changelog

This project uses Conventional Commits and `python-semantic-release` to generate
release notes for PyPI releases.

Data-only refresh commits such as `chore(data): daily refresh [skip ci]` do not
represent software releases and are intentionally excluded from release notes.

## Unreleased

### Added

- Added `pytest-cov` to the development toolchain, with local `make coverage`
  support and CI coverage reporting for the `src/` package.
- Updated development and release tooling pins to their latest compatible stable
  versions, including `build`, `pre-commit`, `pytest-cov`, and
  `python-semantic-release`.
- Fixed the PyPI release workflow so `python-semantic-release` skips its
  internal build step and the pinned job environment performs the package build.
