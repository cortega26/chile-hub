# Plan 153: Extracción remota desde la VM OCI para las fuentes que bloquean GitHub

> **Estado:** DONE (2026-10-26)

## Problema

Cuatro fuentes oficiales responden desde una IP residencial y desde la VM de
OCI, pero **no** desde los runners de GitHub Actions. Consecuencia: cuatro capas
quedaban retenidas todos los días y una de ellas (`resultados_educacionales`)
con datos degradados (3 filas vs 345).

Medido el 2026-10-26 desde `ubuntu@159.112.147.154` (OCI A1, Santiago, AS31898):

| Host | Desde GitHub | Desde la VM |
|:--|:--|:--|
| `datosabiertos.mineduc.cl` | ConnectTimeout | **200**, 43,9 MB |
| `observatorio.ministeriodesarrollosocial.gob.cl` | ConnectTimeout | **200** |
| `www.senado.cl` | 155 diputados, 0 senadores | **200**, 205 registros |
| `sinca.mma.gob.cl` | 403 | **403** — no se arregla |
| `mindicador.cl` | funciona | **reset de TLS** — no se puede mover |

## Decisión

La VM ejecuta cuatro extractores y publica el resultado en un **espejo de
staging público** (`cortega26/chile-hub-remote-staging`). El pipeline lo
descarga justo antes del build.

### Por qué este diseño y no otro

| Alternativa | Por qué se descartó |
|:--|:--|
| Bucket S3/R2 | Vendor + dos credenciales nuevas para 1,6 MB/día |
| La VM commitea a una rama de chile-hub | La VM necesitaría `contents: write` sobre el repo: un compromiso de la VM podría escribir en `main` (sin required reviews). Supply-chain inaceptable |
| nginx de la VM sirviendo los CSV | Acopla el publish de chile-hub al despliegue de pogo-lab y abre una ruta en producción |

El espejo separa la credencial: **la deploy key de la VM solo puede escribir en
un repo que no tiene autoridad sobre el dataset**. El pipeline de chile-hub lo
lee sin credenciales (es público).

### Defensas en el lado que consume

`scripts/apply_remote_staging.py` aplica tres reglas antes de copiar:

1. **Allowlist fija** de cuatro datasets: un nombre nuevo en el espejo no puede
   inyectar archivos en `data/staging/`.
2. **Solo `live`/`monthly`**: un fallback nunca reemplaza el último dato bueno.
3. **`record_count` == filas reales del CSV**: una pareja desincronizada se
   descarta.

Si el espejo no responde o no aporta nada, el pipeline sigue con la extracción
local y decide el gate de publicación (retención). **Nunca falla por el espejo.**

### Operación

- Cron en la VM: `0 8 * * *` (dos horas antes del publish), con `nice`/`ionice`.
- Un solo commit, reescrito con `--force`: el repo se mantiene en ~1,6 MB.
- Log en `~/chile-hub-remote/run.log`; el script no aborta si un extractor falla.
- `git fetch` + `reset --hard main` antes de cada corrida: la VM corre el mismo
  código que CI.

## Verificación

Primera corrida real (2026-10-26T14:00Z), 41 s:

```
OK subdere (dependencia) · OK mineduc_establecimientos · OK mineduc_resultados
OK pobreza · OK autoridades_electas
PUBLICADOS: establecimientos_educacionales (12.898), resultados_educacionales (345),
            pobreza_comunal (690), autoridades_electas (205)
```

`resultados_educacionales` recuperó sus 345 filas y `autoridades_electas` sus 50
senadores.

## Lo que NO resuelve

- **`calidad_aire`**: SINCA devuelve 403 a GitHub, a la VM y a cualquier
  datacenter probado. Sigue en `fallback_to_last_snapshot` (no escala), pero su
  serie no crece desde el runner. Alternativa pendiente de probar: un Worker de
  Cloudflare como proxy.
- **`indicadores`**: mindicador.cl resetea TLS desde la VM. Sigue extrayéndose
  en GitHub; el arreglo del plan 151 ya tolera sus hipos.

## Rollback

1. Quitar el paso "Apply remote staging" de `pipeline-check.yml`.
2. `crontab -r` (o borrar la línea) en la VM.
3. Borrar el repo espejo y la deploy key.

No hay migración de datos ni cambio de esquema.
