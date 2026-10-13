"""Detección de anomalías en series temporales (plan 135)."""

import math
import statistics
from typing import Any

import polars as pl


def detect_series_anomalies(
    df: pl.DataFrame,
    *,
    value_col: str = "valor",
    key_col: str = "codigo_indicador",
    date_col: str = "fecha",
    z_threshold: float = 4.0,
    min_history: int = 4,
) -> list[dict[str, Any]]:
    """Detecta saltos atípicos en el punto más reciente de cada serie temporal.

    Método: z-score robusto (MAD, median absolute deviation) sobre la variación
    logarítmica día a día. Para cada serie (agrupada por ``key_col``, ordenada
    por ``date_col``), compara el log-retorno del punto más reciente contra la
    mediana y el MAD de los log-retornos de referencia (todos los anteriores).
    Se prefiere MAD sobre media±desviación estándar simple porque la media y el
    sigma clásico son frágiles ante los propios outliers que se buscan detectar
    (un solo salto histórico grande infla el sigma y esconde saltos futuros).

    Requiere al menos ``min_history`` log-retornos de referencia antes de
    evaluar — series nuevas o cortas no emiten señal (ver ADR-013).

    Un salto **legítimo** (shock cambiario real, revisión de censo) también
    dispara esta señal, por diseño: la función sólo detecta que el valor es
    estadísticamente atípico frente a su propio histórico reciente, no si es
    "correcto". La decisión de si es un error de fuente o un evento real queda
    para el warning + gate de publicación humano-override (nunca esta función
    aborta nada).

    Returns:
        Lista de anomalías, una por serie con señal, con: ``codigo_indicador``,
        ``fecha`` (del punto anómalo), ``valor``, ``esperado_rango`` (rango de
        valores que NO habría disparado la señal, dado el histórico), ``z_score``,
        ``motivo`` (texto legible).
    """
    anomalies: list[dict[str, Any]] = []
    # Una pasada O(N) en vez de un scan completo por clave O(K·N) (Plan 093).
    # sort + partition_by(maintain_order=True) replica el orden anterior
    # (claves ordenadas, cada serie ordenada por fecha): salida idéntica.
    for series in df.sort(key_col).partition_by(key_col, maintain_order=True):
        key = series[key_col][0]
        series = series.sort(date_col)
        values = series[value_col].to_list()
        dates = series[date_col].to_list()

        log_returns: list[float] = []
        for i in range(1, len(values)):
            prev_value, curr_value = values[i - 1], values[i]
            if prev_value is None or curr_value is None:
                continue
            if prev_value <= 0 or curr_value <= 0:
                continue
            log_returns.append(math.log(curr_value / prev_value))

        last_value = values[-1]
        if len(values) < 2:
            continue  # una sola observación no permite evaluar un par
        penultimate_value = values[-2]

        if (
            penultimate_value is not None
            and last_value is not None
            and penultimate_value > 0
            and last_value > 0
        ):
            # Último par cronológico log-evaluable: flujo actual. log_returns[-1]
            # ES ese par (se procesa en orden), así que la calibración del
            # Plan 054 (z_threshold=4.0, cero falsos positivos en 506 registros)
            # queda intacta.
            if len(log_returns) < min_history + 1:
                continue  # no hay suficiente histórico de referencia + el punto a evaluar

            reference = log_returns[:-1]
            last_return = log_returns[-1]
            median_ref = statistics.median(reference)
            mad = statistics.median([abs(r - median_ref) for r in reference])
            if mad == 0:
                continue  # serie perfectamente constante; sin base para z-score

            z_score = 0.6745 * (last_return - median_ref) / mad
            if abs(z_score) <= z_threshold:
                continue

            prev_value = penultimate_value
            low = prev_value * math.exp(median_ref - z_threshold * mad / 0.6745)
            high = prev_value * math.exp(median_ref + z_threshold * mad / 0.6745)
            motivo = (
                f"Salto atípico en '{key}' el {dates[-1]}: valor {last_value} "
                f"implica un log-retorno diario de {last_return:.4f} vs. mediana "
                f"histórica de referencia {median_ref:.4f} (MAD={mad:.4f}, "
                f"z={z_score:.2f}, umbral={z_threshold}). Rango esperado sin "
                f"señal: [{round(low, 4)}, {round(high, 4)}]."
            )
        else:
            # Último par NO log-evaluable (valor ≤ 0, común en la variación
            # mensual del IPC): detector de nivel sobre los valores previos.
            # Plan 074: antes se evaluaba el último par ADMITIDO (viejo) pero
            # se reportaba con la fecha/valor del punto nuevo — señal mal
            # atribuida, justo el guard del valor scrapeado del INE.
            levels = [v for v in values[:-1] if v is not None]
            if len(levels) < min_history + 1:
                continue
            median_level = statistics.median(levels)
            mad_level = statistics.median([abs(v - median_level) for v in levels])

            if mad_level == 0:
                # Niveles previos constantes: el MAD no da base para z-score,
                # pero un último valor distinto de la mediana ES una ruptura
                # obvia (P2 de la review del Plan 074). Se reporta con z-score
                # infinito y motivo de ruptura de serie constante. Ej.:
                # [100, 100, 100, 100, 100, 0] — el 0 es claramente anómalo.
                if last_value == median_level:
                    continue
                low = min(levels)
                high = max(levels)
                motivo = (
                    f"Salto atípico en '{key}' el {dates[-1]}: valor {last_value} "
                    f"vs. serie de niveles previos constante en {median_level:.4f} "
                    f"(MAD=0, ruptura de serie constante, umbral={z_threshold}). "
                    f"Rango esperado sin señal: [{round(low, 4)}, {round(high, 4)}]."
                )
                z_score = None  # MAD=0: sin base de z-score; la ruptura es obvia
            else:
                z_score = 0.6745 * (last_value - median_level) / mad_level
                if abs(z_score) <= z_threshold:
                    continue
                low = median_level - z_threshold * mad_level / 0.6745
                high = median_level + z_threshold * mad_level / 0.6745
                motivo = (
                    f"Salto atípico en '{key}' el {dates[-1]}: valor {last_value} "
                    f"vs. mediana de niveles previos {median_level:.4f} "
                    f"(MAD={mad_level:.4f}, z={z_score:.2f}, umbral={z_threshold}). "
                    f"Rango esperado sin señal: [{round(low, 4)}, {round(high, 4)}]."
                )

        anomalies.append(
            {
                "codigo_indicador": key,
                "fecha": dates[-1],
                "valor": last_value,
                "esperado_rango": [round(low, 4), round(high, 4)],
                "z_score": round(z_score, 2) if z_score is not None else None,
                "motivo": motivo,
            }
        )
    return anomalies
