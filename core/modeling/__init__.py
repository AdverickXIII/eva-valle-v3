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
from core.modeling.classifications import (
    CLASIFICACION,
    get_classifications,
    get_classifications_dataframe,
)
from core.modeling.conceptual_map import (
    MAPA_CONCEPTUAL,
    get_conceptual_map,
)
from core.modeling.data_dictionary import (
    DICCIONARIO,
    get_data_dictionary,
    get_data_dictionary_dataframe,
)
from core.modeling.hierarchies import (
    generate_crop_hierarchy,
    generate_temporal_hierarchy,
    generate_territorial_hierarchy,
)
from core.modeling.pipeline import run_conceptual_modeling
from core.modeling.surrogate_key import (
    NATURAL_KEY_COLUMNS,
    generate_surrogate_key,
    validate_natural_key,
)
from core.modeling.type_reconversion import reconvert_types

__all__ = [
    "CLASIFICACION",
    "DICCIONARIO",
    "MAPA_CONCEPTUAL",
    "NATURAL_KEY_COLUMNS",
    "generate_crop_hierarchy",
    "generate_surrogate_key",
    "generate_temporal_hierarchy",
    "generate_territorial_hierarchy",
    "get_classifications",
    "get_classifications_dataframe",
    "get_conceptual_map",
    "get_data_dictionary",
    "get_data_dictionary_dataframe",
    "reconvert_types",
    "run_conceptual_modeling",
    "validate_natural_key",
]
