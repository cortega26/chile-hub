#!/usr/bin/env bash
# Reproduce los "Done criteria" de plans/archive/059-publicacion-huggingface-hub.md
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echo "-- make build && publish_hf_dataset.py --dry-run lista 17 parquet --"
make build >/dev/null
DRY_RUN_OUTPUT="$(.venv/bin/python scripts/publish_hf_dataset.py --dry-run)"
echo "$DRY_RUN_OUTPUT"
test "$(echo "$DRY_RUN_OUTPUT" | grep -c 'data/.*\.parquet')" = "17"

echo "-- el dry-run NO lista datasets del carril candidate --"
test "$(echo "$DRY_RUN_OUTPUT" | grep -c 'delincuencia_comunal\|autoridades_locales\|geometria_comunal\|perfil_territorial_comunal\|consumo_electrico_comunal')" = "0"
git checkout -- data/normalized/ README.md index.html 2>/dev/null || true
make sync-docs >/dev/null

echo "-- docs/hf/dataset-card.md con placeholder --"
test "$(grep -c '{{DATASET_TABLE}}' docs/hf/dataset-card.md)" = "1"

echo "-- pypi-release.yml tiene job hf-publish con needs/secret/outputs --"
.venv/bin/python -c "
import yaml
d = yaml.safe_load(open('.github/workflows/pypi-release.yml'))
assert 'hf-publish' in d['jobs']
assert d['jobs']['hf-publish']['needs'] == 'release'
assert 'HF_TOKEN' in str(d['jobs']['hf-publish'])
assert 'released' in d['jobs']['release']['outputs']
assert 'ready' in d['jobs']['release']['outputs']
print('job ok')
"

echo "-- pytest tests/test_ci_config.py --"
.venv/bin/pytest tests/test_ci_config.py -v

echo "-- make lint && make format-check --"
make lint
make format-check

echo "-- sync_docs.py --check --"
.venv/bin/python scripts/sync_docs.py --check

echo "-- make doctor --"
make doctor

echo "Plan 059: OK"
