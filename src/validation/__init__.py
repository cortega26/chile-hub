"""Validadores de chile-hub — fachada del paquete (plan 135).

Move-only desde `validation.py` (AST-hash verificado): la superficie
`from src.validation import validate_x` no cambia. Un módulo por dominio;
el checker de registro (§5) escanea las DEFINICIONES del paquete.
"""

from ._anomalias import detect_series_anomalies as detect_series_anomalies
from ._clima import validate_precipitaciones_dgac as validate_precipitaciones_dgac
from ._constants import _CATEGORIAS_VALIDAS as _CATEGORIAS_VALIDAS
from ._constants import _CHILE_LAT_MAX as _CHILE_LAT_MAX
from ._constants import _CHILE_LAT_MIN as _CHILE_LAT_MIN
from ._constants import _CHILE_LON_MAX as _CHILE_LON_MAX
from ._constants import _CHILE_LON_MIN as _CHILE_LON_MIN
from ._constants import EXPECTED_INDICATOR_CODES as EXPECTED_INDICATOR_CODES
from ._constants import EXPECTED_LIVE_COMUNAS_COUNT as EXPECTED_LIVE_COMUNAS_COUNT
from ._constants import FALLBACK_COMUNAS_COUNT as FALLBACK_COMUNAS_COUNT
from ._constants import VALID_CARGOS_AUTORIDADES_ELECTAS as VALID_CARGOS_AUTORIDADES_ELECTAS
from ._constants import VALID_ESTADO_LEGAL as VALID_ESTADO_LEGAL
from ._dpa import validate_comunas as validate_comunas
from ._dpa import validate_provincias as validate_provincias
from ._dpa import validate_regiones as validate_regiones
from ._economia import validate_consumo_electrico_comunal as validate_consumo_electrico_comunal
from ._economia import validate_empresas as validate_empresas
from ._economia import validate_finanzas_municipales as validate_finanzas_municipales
from ._economia import validate_indicadores as validate_indicadores
from ._economia import validate_pobreza_comunal as validate_pobreza_comunal
from ._educacion import (
    validate_establecimientos_educacionales as validate_establecimientos_educacionales,
)
from ._educacion import validate_resultados_educacionales as validate_resultados_educacionales
from ._helpers import _add_expected_warning as _add_expected_warning
from ._helpers import _duplicate_count as _duplicate_count
from ._helpers import _expected_dv_vectorized as _expected_dv_vectorized
from ._helpers import _invalid_fixed_length_count as _invalid_fixed_length_count
from ._helpers import _missing_columns as _missing_columns
from ._helpers import _negative_numeric_count as _negative_numeric_count
from ._helpers import _percentage_out_of_bounds_count as _percentage_out_of_bounds_count
from ._helpers import _unknown_codes as _unknown_codes
from ._helpers import _validate_ruts_column as _validate_ruts_column
from ._poblacion import validate_censo_comunal as validate_censo_comunal
from ._poblacion import validate_censo_hogares_viviendas as validate_censo_hogares_viviendas
from ._poblacion import validate_estadisticas_vitales as validate_estadisticas_vitales
from ._politica import validate_autoridades_electas as validate_autoridades_electas
from ._politica import validate_distritos_electorales as validate_distritos_electorales
from ._politica import validate_partidos_politicos as validate_partidos_politicos
from ._salud import validate_establecimientos_salud as validate_establecimientos_salud
from ._territorio import validate_calidad_aire as validate_calidad_aire
from ._territorio import validate_geometria_comunal as validate_geometria_comunal
from ._territorio import validate_indicadores_urbanos_siedu as validate_indicadores_urbanos_siedu
from ._territorio import validate_perfil_territorial_comunal as validate_perfil_territorial_comunal
from ._territorio import validate_permisos_edificacion as validate_permisos_edificacion
from ._territorio import validate_puntos_interes as validate_puntos_interes
