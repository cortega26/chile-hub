# Contributing

Thanks for helping keep chile-hub reliable.

## Local Checks

Run the smallest useful checks before opening a pull request:

```bash
make lint
make format-check
make test
```

For changes that affect generated public files, run:

```bash
make build
make verify
make verify-landing
```

## Data Changes

New datasets must follow `AGENTS.md`: evaluate source rights first, add an extractor, write staging metadata, validate in `src/validation.py`, wire the build, add tests, update CI, and document the dataset.

Never edit `data/normalized/` by hand. Regenerate it through the pipeline.

## Pull Requests

Use conventional commit prefixes in commit titles when possible, such as `fix:`, `feat:`, `docs:`, or `chore:`. Releases are generated from commit history after the full pipeline passes.
