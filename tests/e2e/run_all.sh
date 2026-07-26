#!/usr/bin/env bash
# Corre, en orden, los verify_*.sh de todos los planes ya marcados DONE en esta cola.
# Ver spec.md (raíz del repo) para el orden y tests/e2e/README.md para el contrato.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PLANS=(058 057 050 051 054 059 063)

for plan in "${PLANS[@]}"; do
  script="verify_${plan}.sh"
  if [[ ! -f "$script" ]]; then
    echo "skip: ${script} no existe todavia (plan ${plan} no completado)"
    continue
  fi
  echo "=== Plan ${plan} ==="
  "./${script}"
  echo
done

echo "=== make doctor (regresion global) ==="
(cd ../.. && make doctor)
