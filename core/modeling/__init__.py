"""
Modulo de modelado conceptual del proyecto eva-valle-v3.0.

Fachada que expone las funciones principales del Paso 3.

Uso:
    from core.modeling import run_conceptual_modeling, get_data_dictionary

    # Ejecutar el pipeline completo
    df_modelo, artefactos = run_conceptual_modeling()

    # Acceder al diccionario de variables
    diccionario = get_data_dictionary()
"""
from core.modeling.pipeline import run_conceptual_modeling
from core.modeling.data_dictionary import (
    DICCIONARIO,
    get_data_dictionary,
    get_data_dictionary_dataframe,
)
from core.modeling.classifications import (
    CLASIFICACION,
    get_classifications,
    get_classifications_dataframe,
)
from core.modeling.conceptual_map import (
    MAPA_CONCEPTUAL,
    get_conceptual_map,
)
from core.modeling.surrogate_key import (
    NATURAL_KEY_COLUMNS,
    generate_surrogate_key,
    validate_natural_key,
)
from core.modeling.hierarchies import (
    generate_territorial_hierarchy,
    generate_crop_hierarchy,
    generate_temporal_hierarchy,
)
from core.modeling.type_reconversion import reconvert_types

__all__ = [
    "run_conceptual_modeling",
    "DICCIONARIO",
    "get_data_dictionary",
    "get_data_dictionary_dataframe",
    "CLASIFICACION",
    "get_classifications",
    "get_classifications_dataframe",
    "MAPA_CONCEPTUAL",
    "get_conceptual_map",
    "NATURAL_KEY_COLUMNS",
    "generate_surrogate_key",
    "validate_natural_key",
    "generate_territorial_hierarchy",
    "generate_crop_hierarchy",
    "generate_temporal_hierarchy",
    "reconvert_types",
]
