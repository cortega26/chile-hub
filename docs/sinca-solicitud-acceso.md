# Solicitud de acceso técnico a datos del SINCA

> **Estado:** borrador listo para revisión del mantenedor. **No enviado.**
> El envío, la firma y cualquier dato de contacto son decisión y
> responsabilidad del titular.
>
> **Canal sugerido:** OIRS del Ministerio del Medio Ambiente (formulario
> oficial / oficina de partes). Si confirman un correo institucional de SINCA,
> usarlo y adjuntar este texto. No se inventa una dirección.

---

**Para:** Ministerio del Medio Ambiente — Sistema de Información Nacional de
Calidad del Aire (SINCA)
**Asunto:** Solicitud de acceso automatizado de bajo volumen al listado de
monitoreo (`listadomapa2k19`) — proyecto abierto chile-hub

Estimados:

Me presento: soy Carlos Ortega, mantenedor de **chile-hub**
(https://github.com/cortega26/chile-hub), un proyecto abierto bajo licencia MIT
que reúne, normaliza y publica datos públicos chilenos —entre ellos, calidad del
aire— para que investigadores, estudiantes y organismos puedan usarlos sin
reconstruir cada fuente. El proyecto no es comercial, no vende datos y atribuye
la fuente en cada capa publicada.

**Qué usamos.** El listado JSON que alimenta el mapa público de SINCA:
`https://sinca.mma.gob.cl/index.php/json/listadomapa2k19/`. De ahí tomamos los
promedios diarios por estación y contaminante, que ya son públicos en su sitio.

**Cómo lo usamos.** Una petición automatizada al día (≈1,5 MB), desde un flujo de
integración continua, con caché local para no repetir descargas. El resultado se
normaliza, se valida contra la fuente y se publica junto al enlace a SINCA, sin
interpolar ni imputar valores.

**El problema.** Desde el 15–16 de octubre de 2026 ese endpoint responde
`HTTP 403 Forbidden` (Apache, 199 bytes) a los rangos de IP de GitHub Actions.
Verificamos que el mismo endpoint responde `200` con normalidad desde una
conexión residencial chilena, y que el 403 no depende del cliente: ocurre con
`curl`, con navegadores reales (Chromium headless) y desde cuatro redes distintas
(Azure/GitHub, Oracle Cloud, Cloudflare y Fly.io). El detalle técnico está en el
anexo.

No interpretamos esto como una falla: entendemos que puede ser una política
deliberada de protección. Por eso escribimos en vez de buscar rodeos.

**Qué solicitamos** (en orden de preferencia, cualquiera nos sirve):

1. Un **archivo de descarga en bloque** (CSV o JSON) del histórico por estación y
   contaminante, si ya existe o puede publicarse.
2. **Autorización para los rangos de IP** de nuestro flujo de integración,
   documentando el User-Agent (`chile-hub/<versión> (+URL del proyecto)`).
3. Un **endpoint con credencial de bajo volumen** (token o API key), si prefieren
   controlar el acceso.
4. Si existe un **canal oficial de descarga** que no hayamos encontrado, la
   indicación de cuál es.

**Compromisos.** Identificarnos con un User-Agent explícito; una petición diaria
como máximo; respetar `robots.txt`, los términos de uso y la licencia que nos
indiquen; dejar de usar el endpoint de inmediato si nos lo solicitan; y citar a
SINCA y al MMA como fuente en todo artefacto derivado.

Quedo atento a cualquier requisito adicional (formulario, carta de la institución,
identificación) para formalizar la solicitud por el canal que corresponda.

Muchas gracias por el trabajo de publicación: es la razón por la que este
proyecto existe.

Atentamente,
**Carlos Ortega** — mantenedor de chile-hub
ORCID: https://orcid.org/0009-0000-3470-6181
Correo: *(completar antes de enviar)*

---

## Anexo técnico — evidencia (2026-10-26)

Endpoint: `GET https://sinca.mma.gob.cl/index.php/json/listadomapa2k19/`

| Cliente / red | Resultado |
|:--|:--|
| Conexión residencial (Chile) — `curl` | **200**, 1.553.876 B |
| GitHub Actions (Azure) — `requests` | 403, 199 B |
| Oracle Cloud, Santiago — `curl` | 403, 199 B |
| Oracle Cloud — `curl_cffi` impersonando Chrome 124 y Safari 17 | 403, 199 B (idéntico) |
| Oracle Cloud — `scrapling.Fetcher` | 403, 199 B |
| Oracle Cloud — `scrapling.StealthyFetcher` (Chromium 149 headless) | 403, 198 B |
| Cloudflare Workers | 403, 199 B |
| Fly.io, São Paulo | 403, 199 B |

Comprobaciones adicionales, todas negativas: el 403 aplica a **todo el host**
(no solo a la ruta JSON); `http://` redirige a HTTPS; ambas direcciones IP del
registro A responden igual; la VM de prueba no tiene ruta IPv6.

Conclusión: el bloqueo es por **IP de origen**, no por cliente ni por firma TLS.

## Notas para el mantenedor (no forman parte de la carta)

- No enviar sin revisar el tono y completar el correo.
- No adjuntar datos personales, RUT ni documentos que no pida el canal oficial.
- Si responden con un formulario, conservar el comprobante **fuera del repo**.
- Si la respuesta es negativa o no hay respuesta en 30 días, la decisión vigente
  (retener la capa en su última versión buena) sigue siendo válida y no requiere
  cambios técnicos.
