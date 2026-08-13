"""Reintentos HTTP con backoff exponencial para extractores de chile-hub."""

from __future__ import annotations

from typing import Any, Callable

import requests
from tenacity import (
    nap,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)


def _is_retryable(exc: BaseException) -> bool:
    """True para errores de red transitorios y respuestas 5xx; False para 4xx y otros."""
    if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        resp = getattr(exc, "response", None)
        return resp is not None and resp.status_code >= 500
    # curl_cffi comparte nombres de excepción pero no hereda de requests — soporte opcional
    try:
        from curl_cffi.requests import exceptions as cffi_exc

        if isinstance(exc, (cffi_exc.ConnectionError, cffi_exc.Timeout)):
            return True
    except ImportError:
        pass
    return False


def fetch_with_retry(
    url: str,
    *,
    get_fn: Callable[..., Any] = requests.get,
    max_attempts: int = 3,
    sleep: Callable[[float], Any] = nap.sleep,
    **kwargs: Any,
) -> Any:
    """HTTP GET con reintentos exponenciales para errores transitorios.

    Reintenta en ConnectionError, Timeout y respuestas 5xx con backoff 2→4→8 s.
    Los errores 4xx se propagan sin reintentar (son errores del cliente, no del servidor).
    Retorna el objeto Response de get_fn — compatible con el protocolo de contexto
    (``with fetch_with_retry(url) as r:``). Soporta tanto requests como curl_cffi.

    Args:
        url: URL a descargar.
        get_fn: Función GET a invocar (requests.get por defecto; acepta curl_cffi.requests.get).
        max_attempts: Número máximo de intentos, incluyendo el primero.
        sleep: Función de espera entre reintentos (inyectable en tests — ver
            Plan 080: tenacity captura nap.sleep en import-time, así que el
            patch directo no surte efecto).
        **kwargs: Parámetros adicionales para get_fn (timeout, headers, params, etc.).
    """

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception(_is_retryable),
        reraise=True,
        sleep=sleep,
    )
    def _attempt() -> Any:
        resp = get_fn(url, **kwargs)
        if resp.status_code >= 500:
            resp.raise_for_status()
        return resp

    return _attempt()
