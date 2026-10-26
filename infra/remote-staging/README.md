# Staging remoto (VM OCI)

Cuatro fuentes oficiales bloquean el egress de GitHub Actions y responden desde
esta VM (detalle y evidencia en [`plans/153-extraccion-remota-vm.md`](../../plans/153-extraccion-remota-vm.md)).
Este directorio contiene el script que la VM ejecuta a diario y el
procedimiento para reconstruirla.

| Dataset | Fuente | Bloqueo desde GitHub |
|:--|:--|:--|
| `establecimientos_educacionales` | MINEDUC | timeout |
| `resultados_educacionales` | MINEDUC | timeout |
| `pobreza_comunal` | MDS | timeout |
| `autoridades_electas` | Senado | 155 diputados, 0 senadores |

El resultado se publica en un espejo público que el pipeline copia justo antes
del build, con allowlist y validaciones en `scripts/apply_remote_staging.py`.

## Instalación desde cero

```bash
# 1. Dependencias del sistema
sudo apt-get install -y unrar
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Repositorio y entorno (mismas versiones que CI: uv.lock)
git clone --depth 1 https://github.com/cortega26/chile-hub.git ~/chile-hub-remote/repo
cd ~/chile-hub-remote/repo && uv sync --extra pipeline --frozen

# 3. Espejo (deploy key con escritura SOLO en ese repo)
ssh-keygen -t ed25519 -N "" -C "chile-hub-remote-staging@vm" -f ~/.ssh/chile_hub_staging
#   → alta de la clave pública en cortega26/chile-hub-remote-staging (write)
GIT_SSH_COMMAND="ssh -i $HOME/.ssh/chile_hub_staging -o IdentitiesOnly=yes" \
  git clone git@github.com:cortega26/chile-hub-remote-staging.git ~/chile-hub-remote/mirror

# 4. Script y cron
install -m 755 run.sh ~/chile-hub-remote/run.sh
( crontab -l 2>/dev/null | grep -v chile-hub-remote/run.sh; \
  echo "0 8 * * * /home/ubuntu/chile-hub-remote/run.sh >/dev/null 2>&1" ) | crontab -
```

## Qué hace cada corrida

1. `git fetch` + `reset --hard origin/main`: corre el mismo código que CI.
2. `uv sync --extra pipeline --frozen`: alinea el entorno si cambió `uv.lock`.
3. Corre cuatro extractores con `nice`/`ionice`; un fallo no aborta los demás.
4. Copia al espejo **solo** los datasets con `source_mode` live/monthly y
   `record_count` consistente. Un fallback nunca pisa el dato bueno.
5. Reescribe el espejo con un único commit (`--amend` + `--force`): 556 KB fijos.

Log en `~/chile-hub-remote/run.log` (se recorta a 1 MB).

## Si la VM se cae

No hay acción urgente: el pipeline detecta el espejo inaccesible, sigue con la
extracción local y el gate de publicación retiene esas capas en su última
versión buena. Se recupera sola al volver la VM.

## Rollback

1. Quitar el paso `Apply remote staging (VM egress)` de `pipeline-check.yml`.
2. `crontab -r` en la VM (o borrar esa línea).
3. Borrar el repo espejo y su deploy key.
