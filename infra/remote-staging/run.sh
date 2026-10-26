#!/usr/bin/env bash
# Extracción remota de chile-hub desde la VM OCI (Santiago).
#
# Motivo: cuatro hosts oficiales bloquean el egress de GitHub Actions pero
# responden desde esta red (verificado el 2026-10-26 desde esta misma VM).
# El resultado se publica en el espejo `chile-hub-remote-staging`, que el
# pipeline de GitHub descarga antes del build.
#
# Reglas:
#   - Solo se publica un dataset cuyo source_mode quedó live/monthly. Un
#     fallback JAMÁS sobrescribe el último dato bueno del espejo.
#   - Un fallo de un extractor no aborta los demás.
#   - Carga baja: corre a las 08:00 UTC, con nice/ionice, antes del publish.

set -uo pipefail

ROOT="$HOME/chile-hub-remote"
REPO="$ROOT/repo"
MIRROR="$ROOT/mirror"
LOG="$ROOT/run.log"
export PATH="$HOME/.local/bin:$PATH"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >>"$LOG"; }

# Recorte simple: el log no debe crecer sin límite en una máquina de producción.
if [ -f "$LOG" ] && [ "$(stat -c%s "$LOG" 2>/dev/null || echo 0)" -gt 1048576 ]; then
  tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

log "=== inicio ==="

cd "$REPO" || { log "FATAL sin repo"; exit 1; }
if ! git fetch --depth 1 origin main -q || ! git reset --hard origin/main -q; then
  log "WARN no se pudo actualizar el repo; se usa la copia local"
fi
log "repo en $(git rev-parse --short HEAD)"

# Auto-sanación del entorno: un bump de uv.lock deja el venv desfasado del
# código y el extractor correría con versiones distintas a CI.
if uv sync --extra pipeline --frozen >>"$LOG" 2>&1; then
  log "OK uv sync (entorno alineado con uv.lock)"
else
  log "WARN uv sync falló; se usa el entorno existente"
fi

# Dependencia: comunas.csv para los extractores que resuelven CUT.
if PYTHONPATH=src ./.venv/bin/python src/extractors/subdere_extractor.py >>"$LOG" 2>&1; then
  log "OK subdere (dependencia)"
else
  log "WARN subdere falló; se continúa"
fi

run() {
  local name="$1"; shift
  if nice -n 19 ionice -c3 "$@" >>"$LOG" 2>&1; then
    log "OK $name"
  else
    log "FAIL $name"
  fi
}

run mineduc_establecimientos ./.venv/bin/python src/extractors/mineduc_establecimientos_extractor.py
run mineduc_resultados ./.venv/bin/python src/extractors/mineduc_resultados_extractor.py
run pobreza ./.venv/bin/python src/extractors/pobreza_extractor.py

# autoridades_electas necesita scrapling (anti-403 en camara.cl/senado.cl).
# Se usa el mismo entorno efímero pinneado que CI.
run autoridades_electas uv run --no-project \
  --with "scrapling[fetchers]==0.4.10" --with polars==1.44.2 \
  --with requests==2.34.2 --with structlog==26.1.0 --with tenacity==9.1.4 \
  --with curl_cffi==0.16.3 --with defusedxml==0.7.1 \
  python src/extractors/autoridades_electas_extractor.py

# Publicar solo lo que quedó live. Un fallback sobrescribiría el último dato
# bueno y el pipeline lo rechazaría después por caída de record_count.
python3 - "$REPO" "$MIRROR" <<'PY' >>"$LOG" 2>&1
import json
import shutil
import sys
from pathlib import Path

repo, mirror = Path(sys.argv[1]), Path(sys.argv[2])
targets = [
    "establecimientos_educacionales",
    "resultados_educacionales",
    "pobreza_comunal",
    "autoridades_electas",
]
dest = mirror / "data" / "staging"
dest.mkdir(parents=True, exist_ok=True)
published = []
for name in targets:
    meta = repo / "data" / "staging" / f"{name}.metadata.json"
    csv = repo / "data" / "staging" / f"{name}.csv"
    if not (meta.exists() and csv.exists()):
        print(f"SKIP {name}: sin archivos")
        continue
    mode = json.loads(meta.read_text(encoding="utf-8")).get("source_mode")
    if mode not in {"live", "monthly"}:
        print(f"SKIP {name}: source_mode={mode}")
        continue
    shutil.copy2(csv, dest / csv.name)
    shutil.copy2(meta, dest / meta.name)
    published.append(name)
(dest / "PUBLISHED.json").write_text(
    json.dumps({"published": sorted(published)}, indent=2) + "\n", encoding="utf-8"
)
print("PUBLICADOS:", published)
PY

cd "$MIRROR" || { log "FATAL sin espejo"; exit 1; }
git add -A
if git diff --cached --quiet; then
  log "sin cambios en el espejo"
  log "=== fin ==="
  exit 0
fi
git -c user.name="chile-hub-remote" -c user.email="remote@chile-hub.invalid" \
  commit -q --amend --allow-empty -m "chile-hub remote staging snapshot"
GIT_SSH_COMMAND="ssh -i $HOME/.ssh/chile_hub_staging -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" \
  git push -q --force origin HEAD:main
log "espejo actualizado $(git rev-parse --short HEAD)"
log "=== fin ==="
