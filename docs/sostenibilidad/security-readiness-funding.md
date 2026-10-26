# Seguridad y readiness para financiamiento — chile-hub

> **Qué es.** Diagnóstico de seguridad basado en señales **operativas** —no en la
> existencia de archivos de configuración— más las brechas justificadas y su
> remediación.
>
> **Qué no es.** No contiene vulnerabilidades explotables sin resolver. Cualquier
> hallazgo de ese tipo va por advisory privado (`SECURITY.md`), nunca por un
> documento público.

- **Consulta:** 2026-10-25 (America/Santiago).
- **Base:** `main` @ `3400c81051019bfd57afd1d10aa32ed554db99e6`.
- **Método:** API de GitHub con la cuenta del mantenedor (solo lectura), OpenSSF
  Scorecard v5.6.0 en contenedor, y los comandos de verificación del repositorio.

## 1. Controles existentes y su estado **operativo**

La diferencia entre "está configurado" y "está funcionando" es el punto de este
documento. Todo lo de la columna "Estado" se comprobó hoy.

| Control | Configurado | Estado operativo comprobado | Evidencia |
|:--|:--|:--|:--|
| CodeQL (Python) | `codeql.yml` en push, PR, merge_group y semanal | **Verde.** 0 alertas abiertas. Última corrida 2026-10-24 `success` | `gh api .../code-scanning/alerts` → 0; `gh run list` |
| Dependabot | pip + GitHub Actions, agrupado, semanal | **Funcionando.** 27 alertas históricas, **todas `fixed`**, 0 abiertas | `gh api .../dependabot/alerts` |
| Dependabot security updates | Habilitado | Activo | `security_and_analysis.dependabot_security_updates: enabled` |
| Secret scanning | Habilitado | **0 alertas** | `gh api .../secret-scanning/alerts` → 0 |
| Push protection | Habilitado | Activo | `security_and_analysis.secret_scanning_push_protection: enabled` |
| Política de divulgación | `SECURITY.md` con advisory privado | Presente y usable | `SECURITY.md` |
| Permisos por defecto del token | `read` | Correcto (mínimo privilegio por defecto) | `gh api .../actions/permissions/workflow` |
| Fijado de acciones por SHA | 57/57 de GitHub y 18/18 de terceros | **Completo** en workflows | OpenSSF Scorecard, check `Pinned-Dependencies` |
| Patrones peligrosos de workflow | — | **Ninguno.** Sin `pull_request_target` ni `issue_comment` | `grep` sobre `.github/workflows/` |
| Revisión de dependencias en PR | `dependency-review.yml` | Activo | `gh run list` (PR de dependabot, `success`) |
| Publicación a PyPI | Trusted publishing OIDC, sin token de larga vida | **Con atestación verificada** | `https://pypi.org/integrity/chile-hub/1.51.0/.../provenance` → HTTP 200, publisher `GitHub`, workflow `pypi-release.yml` |
| Validación del run que dispara el release | `is_trusted_run()` en `pypi-release.yml` | Presente; rechaza runs de otro repositorio | `pypi-release.yml:143–178` |
| Integridad de los datos publicados | `verify_pipeline.py --profile publication` | **Activo y ejerciendo su función**: es la causa de que el publish esté bloqueado desde el 2026-10-15 | Log del run 40200343251 |
| Contratos de esquema | 26 en `contracts/datasets/` | Verificados por `check_companion_paths` y `make doctor` | `make doctor` → exit 0 |
| Gates anti-drift | `sync_docs --check`, `check_agents_sync`, `check_landing_sync` | Verdes hoy | `make doctor` |
| Protección de rama `main` | Historia lineal, sin force-push, sin borrado, conversación resuelta | **Parcial**. Sin revisiones requeridas, sin status checks obligatorios, `enforce_admins: false` | `gh api .../branches/main/protection` |

## 2. OpenSSF Scorecard

Se ejecutó la herramienta oficial (read-only) porque el proyecto no estaba en el
dataset público de Scorecard (la API devolvía 404).

- **Herramienta:** `ghcr.io/ossf/scorecard:latest`, v5.6.0.
- **Commit analizado:** `3400c8105101`.
- **Fecha:** 2026-10-25T22:04:10Z.
- **Puntaje:** **6,2 / 10**.

| Check | Puntaje | Lectura honesta |
|:--|--:|:--|
| Dangerous-Workflow | 10 | Sin patrones peligrosos. Es el check que más importa |
| Vulnerabilities | 10 | 0 vulnerabilidades conocidas |
| Dependency-Update-Tool | 10 | Dependabot activo |
| Security-Policy | 10 | `SECURITY.md` presente |
| License | 10 | MIT detectada |
| Packaging | 10 | Workflow de publicación detectado |
| Maintained | 10 | 30 commits y 10 issues en 90 días |
| Pinned-Dependencies | 8 | 3 comandos `pip install` sin hash en workflows de prueba |
| CI-Tests | 9 | 12 de 13 PR fusionados con CI |
| SAST | 9 | CodeQL no corre en 1 de 13 commits |
| Binary-Artifacts | 9 | `vendor/duckdb/duckdb-mvp.wasm` (legítimo, para el playground) |
| Branch-Protection | 3 | Sin revisiones ni status checks obligatorios |
| **Signed-Releases** | **0** | **Ninguna release de GitHub firmada ni con procedencia** |
| **Token-Permissions** | **0** | Permisos de escritura a nivel de job/top-level en 7 workflows |
| CII-Best-Practices | 0 | Sin badge de OpenSSF |
| Code-Review | 0 | 0 de 27 changesets aprobados |
| Contributors | 0 | Sin organizaciones contribuyentes |
| Fuzzing | 0 | Sin fuzzing |

> **Advertencia metodológica.** El puntaje **no** es un objetivo. Tres de los
> ceros son estructurales e inevitables para un mantenedor único (`Code-Review`,
> `Contributors`, y buena parte de `Token-Permissions`, porque publicar datos
> exige `contents: write`). Optimizarlos sería trabajo cosmético, exactamente lo
> que el plan prohíbe.

## 3. Brechas, priorizadas por riesgo probado

Se aplicó el criterio del plan: riesgo probado, esfuerzo, efecto para usuarios y
compatibilidad con CI. Solo se listan las que resisten ese filtro.

### Brecha 1 — Las releases de GitHub no tienen procedencia (material)

- **Riesgo probado:** el bundle ZIP es el canal de activación principal (189
  descargas acumuladas) y se distribuye con un `.sha256`. Un atacante que pueda
  publicar o modificar una release reemplaza **ambos** archivos de forma
  consistente y la verificación sigue pasando. El checksum protege contra
  corrupción, no contra compromiso.
- **Asimetría que lo hace evidente:** el paquete de PyPI **sí** tiene atestación
  verificable. El artefacto que más se descarga, no.
- **Remediación propuesta (no ejecutada):** añadir un paso
  `actions/attest-build-provenance` al job `release` de
  `.github/workflows/pypi-release.yml`, después de `gh release upload`
  (línea 383), con permisos de job `attestations: write` e `id-token: write`.
  Sujetos: `chile-hub-publishable-bundle.zip`, su `.sha256` y
  `artifact_manifest.json`.
- **Verificación para el consumidor:** `gh attestation verify <archivo> --repo cortega26/chile-hub`.
- **Esfuerzo:** ~6 líneas de YAML + una entrada en `docs/`.
- **Por qué no se ejecutó:** su validación real requiere **una release en
  producción**. No es verificable en local ni en un PR. Un cambio no verificado
  en el workflow más crítico del proyecto es peor que la brecha.

### Brecha 2 — `main` sin revisiones ni status checks obligatorios (aceptada)

- **Riesgo probado:** ninguno hasta hoy. No hay PRs externos activos y el
  mantenedor es único.
- **Costo de cerrarla:** exigir revisiones bloquearía los commits automáticos de
  datos (`[skip ci]`) y la sincronización de docs, que son el mecanismo de
  publicación del proyecto.
- **Decisión recomendada:** **no cambiar**. Documentar como riesgo aceptado con
  controles compensatorios: historia lineal, sin force-push, sin borrado, CI
  obligatorio por convención, y `verify_pipeline.py` como compuerta real.
- **Alternativa si se quisiera endurecer:** activar `enforce_admins` y required
  status checks solo para `main`, excluyendo los jobs de publicación. Requiere
  decisión del mantenedor y una prueba con la merge queue.

### Brecha 3 — `actions: write` y permisos de escritura en 7 workflows (menor)

- **Riesgo probado:** bajo. Son jobs que efectivamente commitean datos o
  disparan otros workflows.
- **Costo de cerrarla:** mover permisos de nivel superior a nivel de job en
  `adoption-stats.yml`, `dependabot-lock.yml`, `dgac-publish.yml` y
  `geometria-comunal.yml`. Cambio de bajo riesgo pero **sin efecto funcional**
  (cada workflow tiene un solo job o ya limita por job).
- **Decisión recomendada:** **no hacerlo ahora.** Sería cosmético.

### Lo que **no** es una brecha (y no debe "arreglarse")

| Señal de Scorecard | Por qué no aplica |
|:--|:--|
| `Code-Review` = 0 | Mantenedor único. Forzar revisiones rompe la publicación automática |
| `Contributors` = 0 | Refleja la realidad; no es un defecto técnico |
| `Fuzzing` = 0 | La superficie de parseo es CSV/XLSX/JSON de fuentes fijas; el costo no se justifica frente al beneficio |
| `Binary-Artifacts` = 9 | El WASM es parte del playground, versionado a propósito |
| `CII-Best-Practices` = 0 | Trámite de badge, sin efecto en seguridad real |
| `Token-Permissions` = 0 | Publicar datos requiere escritura; el puntaje no distingue necesidad de exceso |

## 4. Veredicto

> **Sin trabajo de seguridad nuevo justificado, salvo uno.**
>
> El proyecto está por encima de la media en higiene de cadena de suministro
> (acciones fijadas por SHA, trusted publishing, atestaciones de PyPI, sin
> `pull_request_target`, permisos por defecto en lectura, 0 vulnerabilidades
> abiertas). La única brecha con efecto real para un usuario es la **falta de
> procedencia en las releases de GitHub**, y su arreglo es pequeño pero solo
> verificable en producción.

## 5. Riesgo operativo que domina a todos los anteriores

La publicación programada lleva **10 ejecuciones consecutivas fallidas**
(2026-10-16 → 2026-10-25) y el último snapshot publicado es del **2026-10-15**.
El pipeline hace lo correcto —se niega a publicar datos en fallback— pero el
resultado es que el proyecto lleva diez días sin cumplir su promesa central.

Ningún control de seguridad compensa eso: un consumidor que hoy descargue el
bundle obtiene datos de hace diez días. Está registrado en el issue #195 y es la
evidencia más concreta de riesgo de continuidad del proyecto.

**No se propone remediarlo aquí:** es un problema de fuentes upstream y de
extractores, ya tiene issue propio, y el plan de financiamiento no autoriza
trabajo de ingeniería de datos.

## 6. Reproducibilidad

```bash
# Alertas y configuración (solo lectura, cuenta del mantenedor)
gh api repos/cortega26/chile-hub/code-scanning/alerts --paginate -q '[.[]|select(.state=="open")]|length'
gh api repos/cortega26/chile-hub/dependabot/alerts --paginate -q 'group_by(.state)|map({state:.[0].state,n:length})'
gh api repos/cortega26/chile-hub/secret-scanning/alerts --paginate -q 'length'
gh api repos/cortega26/chile-hub/branches/main/protection
gh api repos/cortega26/chile-hub/actions/permissions/workflow

# OpenSSF Scorecard (la imagen de gcr.io exige billing; usar ghcr.io)
docker run --rm -e GITHUB_AUTH_TOKEN="$(gh auth token)" \
  ghcr.io/ossf/scorecard:latest \
  --repo=github.com/cortega26/chile-hub --show-details --format=json

# Atestación de PyPI
curl -s -o /dev/null -w '%{http_code}\n' \
  "https://pypi.org/integrity/chile-hub/1.51.0/chile_hub-1.51.0-py3-none-any.whl/provenance"

# Estado del pipeline
make doctor
gh run list --workflow=pipeline-check.yml --event=schedule --limit 10
```
