"""Constantes canónicas del pipeline de validación (plan 135)."""

EXPECTED_INDICATOR_CODES = {"uf", "dolar", "euro", "utm", "ipc"}

FALLBACK_COMUNAS_COUNT = 18

EXPECTED_LIVE_COMUNAS_COUNT = 346

# ── Bounding box de Chile continental (incluye isla de Pascua) ─────────────────
_CHILE_LAT_MIN = -56.5

_CHILE_LAT_MAX = -17.0

_CHILE_LON_MIN = -110.0  # Isla de Pascua ~109°W

_CHILE_LON_MAX = -66.0

_CATEGORIAS_VALIDAS = {"amenidad", "comercio", "turismo", "oficina", "oficio"}

VALID_ESTADO_LEGAL = {"constituido", "en_formacion", "disuelto"}

VALID_CARGOS_AUTORIDADES_ELECTAS = {"diputado", "senador"}
