#!/usr/bin/env bash
# Corre, en orden, los verify_*.sh de los planes DONE de la cola actual.
#
# Plan 080: los scripts de planes ARCHIVADOS quedaron congelados en
# plans/archive/e2e/ — sus aserciones de datos vivos se rompen con la
# evolución del pipeline (el verify_059 ya exigió un fix con el Plan 084:
# 17→18 parquets). La decisión es documentada: el registro histórico vive
# en plans/archive/e2e/, no se ejecuta.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PLANS=()

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
