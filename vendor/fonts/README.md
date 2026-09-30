# Tipografías auto-hospedadas

Los `.woff2` de este directorio sirven las tipografías de la landing
(`index.html`) desde el mismo origen del sitio, sin peticiones a Google Fonts
(privacidad: ninguna visita revela IP ni `Referer` a un tercero).

## Origen

Descargados de la API CSS2 de Google Fonts el **2026-09-29** con un user-agent
moderno (Chrome 126), solo el subset `latin`. Cada archivo se pidió por peso y
estilo, preservando el eje óptico (`opsz`) de las fuentes variables; el peso
(`wght`) queda fijado por archivo y declarado en su `@font-face`.

URL base de la API usada (una petición por cara):

```
https://fonts.googleapis.com/css2?family=<familia>:<ejes>&display=swap
```

| Familia | Ejes solicitados | Pesos |
|:---|:---|:---|
| Inter | `ital,opsz,wght@<0\|1>,14..32,<peso>` | 400, 500, 600, 700 + itálicas 400, 600 |
| JetBrains Mono | `ital,wght@<0\|1>,<peso>` | 400, 600 + itálica 400 |
| Source Serif 4 | `ital,opsz,wght@<0\|1>,8..60,<peso>` | 400, 500, 600, 700 + itálicas 400, 600 |

`0` = normal, `1` = itálica. El `unicode-range` latin de cada `@font-face`
(`U+0000-00FF`, `U+0131`, `U+0152-0153`, `U+02BB-02BC`, `U+02C6`, `U+02DA`,
`U+02DC`, `U+0304`, `U+0308`, `U+0329`, `U+2000-206F`, `U+20AC`, `U+2122`,
`U+2191`, `U+2193`, `U+2212`, `U+2215`, `U+FEFF`, `U+FFFD`) cubre el español
completo (tildes y `ñ` incluidos).

## Licencia

Las tres familias son **SIL Open Font License 1.1** (OFL-1.1), que permite
usarlas, modificarlas y redistribuirlas:

- Inter — Copyright (c) 2016 The Inter Project Authors —
  <https://github.com/rsms/inter/blob/master/LICENSE.txt>
- JetBrains Mono — Copyright (c) 2020 The JetBrains Mono Project Authors —
  <https://github.com/JetBrains/JetBrainsMono/blob/master/OFL.txt>
- Source Serif 4 — Copyright (c) 2014-2023 Adobe —
  <https://github.com/adobe-fonts/source-serif/blob/release/LICENSE.md>

## Inventario

| Archivo | Peso | Estilo | SHA-256 |
|:---|:---:|:---:|:---|
| `inter/inter-latin-400.woff2` | 400 | normal | `96b1166d19616a0e0b4ffc1f3cd0a8f20f85b6bb8ed302498639646c772c6c76` |
| `inter/inter-latin-500.woff2` | 500 | normal | `e4eb42c0c9de93b544988c558177afe1509c18b3c3c5044a50609a30f51ff3c4` |
| `inter/inter-latin-600.woff2` | 600 | normal | `0b2a0a5e239ac7c62a3eede7150703d6825fcf69d015c4efc3e37986c57c6b25` |
| `inter/inter-latin-700.woff2` | 700 | normal | `2058e64df11ab765822c2edc82f39b45d0bc202acbd710cdfad26f86df2f89c3` |
| `inter/inter-latin-400-italic.woff2` | 400 | italic | `e6d177df709dc783efd55fdeedea6ae7dd8f860245197bd8a8a0bc829ef66182` |
| `inter/inter-latin-600-italic.woff2` | 600 | italic | `ca2837aeb9d037be5f086ac41e1e2cca53f17bae69972bc6dd593f510e79b557` |
| `jetbrains-mono/jetbrains-mono-latin-400.woff2` | 400 | normal | `14425ba9c695763c1547f48a206b7aa60350a33ae23de09f0407877f3fcd89eb` |
| `jetbrains-mono/jetbrains-mono-latin-600.woff2` | 600 | normal | `400c6bfda18d5d14acad1c15d6dcb9f8e13c015e7286317e0b9a482539bef147` |
| `jetbrains-mono/jetbrains-mono-latin-400-italic.woff2` | 400 | italic | `87ddac4a62229787528cf4ac3fa58137b62a9aec364c44fc0f40470bcda9efba` |
| `source-serif-4/source-serif-4-latin-400.woff2` | 400 | normal | `ba627ffc66e406b09078e06d4a683a6f4dec989b258927ce8f165d046e23bf2f` |
| `source-serif-4/source-serif-4-latin-500.woff2` | 500 | normal | `face7fe474782c71a6542509af01008e40484da73f8f3a2774f4578be0633173` |
| `source-serif-4/source-serif-4-latin-600.woff2` | 600 | normal | `86a8cd5aa414cad7d3e2bbbb7977e69b82d6f9d8f1d5aafa7c7133eb32571910` |
| `source-serif-4/source-serif-4-latin-700.woff2` | 700 | normal | `8db8ecdb9ad0fb0358f9adb81710836fea03373f5cad8ee75c8caaced0f491f7` |
| `source-serif-4/source-serif-4-latin-400-italic.woff2` | 400 | italic | `09147e39b7b7aaf201498b2e8ee7e5fddaf7073cbab42d9b06217e4a9f7fdf78` |
| `source-serif-4/source-serif-4-latin-600-italic.woff2` | 600 | italic | `a73991f26aea1fd32b8d172d29f5c8c86d458ad8671401caacb3fc3fd558b375` |

## Actualizar

1. Re-descargar los `.woff2` con la URL base de arriba (un peso por petición).
2. Actualizar los `@font-face` de `index.html` si cambian familias, pesos o
   nombres de archivo.
3. Actualizar la fecha, el inventario y los hashes de este README.

No hay gate automático de skew entre este directorio y `index.html`; el smoke
test de la landing (`scripts/verify_landing.py`) sí verifica que las fuentes
declaradas se carguen.
