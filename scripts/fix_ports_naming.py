"""
Script de correccion: renombra core/ports/in/ y core/ports/out/
a core/ports/inbound/ y core/ports/outbound/ porque 'in' es
una palabra reservada de Python y no puede usarse como nombre de modulo.

Ejecutar una sola vez: python scripts/fix_ports_naming.py
"""
import shutil
from pathlib import Path

# ── Paso 1: Eliminar las carpetas con nombres problematicos ──────
for old_dir in ["core/ports/in", "core/ports/out"]:
    p = Path(old_dir)
    if p.exists():
        shutil.rmtree(p)
        print(f"[DEL] {old_dir}/")

# ── Paso 2: Recrear los archivos con nombres correctos ───────────

# ═══════════════════════════════════════════════════════════
# core/ports/inbound/__init__.py
# ═══════════════════════════════════════════════════════════
INBOUND_INIT = '''"""
Puertos de ENTRADA (inbound): definen lo que el mundo exterior
(Streamlit, API, CLI) puede solicitar al nucleo de dominio.

Cada puerto es un Protocol (interfaz estructural). Los casos de uso
del nucleo implementan estos protocolos.
"""
from core.ports.inbound.data_loader_port import DataLoaderPort
from core.ports.inbound.audit_port import AuditPort
from core.ports.inbound.analytics_port import AnalyticsPort
from core.ports.inbound.diagnostics_port import DiagnosticsPort
from core.ports.inbound.ml_port import MLPort

__all__ = [
    "DataLoaderPort",
    "AuditPort",
    "AnalyticsPort",
    "DiagnosticsPort",
    "MLPort",
]
'''

# ═══════════════════════════════════════════════════════════
# core/ports/inbound/data_loader_port.py
# ═══════════════════════════════════════════════════════════
DATA_LOADER_PORT = '''"""
Puerto de entrada para carga de datasets.

Define el contrato para cargar los datasets del pipeline:
- Dataset estandarizado (salida del Paso 1+2)
- Dataset con modelo conceptual (salida del Paso 3)

Los Pasos 4, 5, 6 y 7 consumen este puerto al inicio.
"""
from __future__ import annotations

from typing import Protocol

import pandas as pd


class DataLoaderPort(Protocol):
    """Contrato para cargar datasets del pipeline EVA."""

    def load_clean_dataset(self) -> pd.DataFrame:
        """
        Carga el dataset estandarizado del Paso 1+2.

        Returns:
            DataFrame con ~9,032 registros del Valle del Cauca,
            18 columnas, tipos correctos (Int64, float64, str).

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        ...

    def load_model_dataset(self) -> pd.DataFrame:
        """
        Carga el dataset con modelo conceptual del Paso 3.
        Incluye la columna id_registro (llave surrogate).

        Returns:
            DataFrame con ~9,032 registros, 19 columnas
            (18 originales + id_registro).

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        ...

    def get_record_count(self) -> int:
        """
        Retorna el numero de registros del dataset cargado.
        Util para validaciones rapidas sin cargar todo el DataFrame.
        """
        ...
'''

# ═══════════════════════════════════════════════════════════
# core/ports/inbound/audit_port.py
# ═══════════════════════════════════════════════════════════
AUDIT_PORT = '''"""
Puerto de entrada para auditoria de datos.

Define el contrato para ejecutar las 8 auditorias del Paso 2:
2.1 Estructura, 2.2 Nulos, 2.3 Duplicados, 2.4 Territorial,
2.5 Temporal, 2.6 Rangos, 2.7 Consistencia logica, 2.8 Reporte.
"""
from __future__ import annotations

from typing import Protocol

import pandas as pd


class AuditPort(Protocol):
    """Contrato para ejecutar auditorias de calidad de datos."""

    def run_all_audits(self, df: pd.DataFrame) -> list[dict]:
        """
        Ejecuta las 8 auditorias secuenciales sobre el DataFrame.

        Args:
            df: DataFrame estandarizado del Paso 1.

        Returns:
            Lista de hallazgos, cada uno con:
            {codigo, severidad, descripcion, detalle}.
        """
        ...

    def run_structure_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.1: columnas esperadas, tipos, memoria."""
        ...

    def run_nulls_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.2: cobertura de nulos por columna."""
        ...

    def run_duplicates_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.3: duplicados exactos y por clave natural."""
        ...

    def run_territorial_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.4: coherencia codigos/nombres territoriales."""
        ...

    def run_temporal_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.5: anos, periodos, coherencia cruzada."""
        ...

    def run_ranges_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.6: rangos validos, outliers 3xIQR."""
        ...

    def run_logic_audit(self, df: pd.DataFrame) -> list[dict]:
        """Auditoria 2.7: reglas de negocio R1-R6."""
        ...
'''

# ═══════════════════════════════════════════════════════════
# core/ports/inbound/analytics_port.py
# ═══════════════════════════════════════════════════════════
ANALYTICS_PORT = '''"""
Puerto de entrada para analisis descriptivo profundo.

Define el contrato para ejecutar los 12 analisis del Paso 4:
4.3 Descriptiva, 4.4 Distribuciones, 4.5 Outliers, 4.6 Concentracion,
4.7 Series de tiempo, 4.8 Estacionalidad, 4.9 LQ, 4.10 Shannon,
4.11 Elasticidades, 4.12 Inferencial, 4.13 CAGR, 4.14 Ex-Cana.
"""
from __future__ import annotations

from typing import Any, Protocol

import pandas as pd


class AnalyticsPort(Protocol):
    """Contrato para ejecutar analisis descriptivos del Paso 4."""

    def descriptive_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.3: Momentos, percentiles, CV para las 4 metricas."""
        ...

    def distribution_fitting(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.4: KS-test para Normal, Lognormal, Gamma sobre rendimiento."""
        ...

    def multivariate_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.5: Isolation Forest sobre las 4 metricas."""
        ...

    def concentration_analysis(
        self,
        df: pd.DataFrame,
        group: str = "cultivo",
        value: str = "produccion_t",
    ) -> dict[str, Any]:
        """4.6: HHI, Gini (CORREGIDO), datos para curva de Lorenz."""
        ...

    def time_series_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.7: STL + Dickey-Fuller sobre produccion total semestral."""
        ...

    def seasonality_ab(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.8: Wilcoxon A vs B en cultivos transitorios."""
        ...

    def location_quotient(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.9: LQ por municipio x grupo de cultivo."""
        ...

    def shannon_diversity(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.10: Shannon-Wiener por municipio."""
        ...

    def elasticity_analysis(self, df: pd.DataFrame) -> dict[str, float]:
        """4.11: Regresion log-log produccion vs area."""
        ...

    def inferential_test(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.12: Kruskal-Wallis rendimiento por municipio."""
        ...

    def cagr_by_crop(self, df: pd.DataFrame) -> pd.DataFrame:
        """4.13: CAGR por cultivo 2019-2024."""
        ...

    def ex_cana_analysis(self, df: pd.DataFrame) -> dict[str, Any]:
        """4.14: HHI/Gini excluyendo Cultivos Tropicales Tradicionales."""
        ...
'''

# ═══════════════════════════════════════════════════════════
# core/ports/inbound/diagnostics_port.py
# ═══════════════════════════════════════════════════════════
DIAGNOSTICS_PORT = '''"""
Puerto de entrada para analisis diagnostico.

Define el contrato para ejecutar los 5 analisis del Paso 6:
6.1 Correlacion, 6.2 Comparacion grupos, 6.3 K-Means,
6.4 Arbol de decision, 6.5 Shock 2020.
"""
from __future__ import annotations

from typing import Any, Protocol

import pandas as pd


class DiagnosticsPort(Protocol):
    """Contrato para ejecutar analisis diagnosticos del Paso 6."""

    def correlation_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """6.1: Matriz Spearman + scatterplots clave."""
        ...

    def group_comparison(self, df: pd.DataFrame) -> dict[str, Any]:
        """6.2: Mann-Whitney U (Transitorio vs Permanente)."""
        ...

    def municipality_segmentation(self, df: pd.DataFrame) -> pd.DataFrame:
        """6.3: K-Means clustering de municipios."""
        ...

    def root_cause_analysis(self, df: pd.DataFrame) -> pd.Series:
        """6.4: Arbol de decision regresor (importancia de variables)."""
        ...

    def shock_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """6.5: Variacion interanual 2020 vs tendencia."""
        ...
'''

# ═══════════════════════════════════════════════════════════
# core/ports/inbound/ml_port.py
# ═══════════════════════════════════════════════════════════
ML_PORT = '''"""
Puerto de entrada para Machine Learning predictivo.

Define el contrato para ejecutar los modelos del Paso 7:
7.1 Feature engineering, 7.2 Regresion RF, 7.3 Clasificacion RF,
7.4 Holt-Winters, 7.5 Scoring.
"""
from __future__ import annotations

from typing import Any, Protocol

import pandas as pd


class MLPort(Protocol):
    """Contrato para ejecutar modelos predictivos del Paso 7."""

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """7.1: Feature engineering (lags, target encoding, log)."""
        ...

    def train_regression(self, df: pd.DataFrame) -> dict[str, Any]:
        """7.2: Random Forest Regressor sobre log(produccion)."""
        ...

    def train_classification(self, df: pd.DataFrame) -> dict[str, Any]:
        """7.3: Random Forest Classifier para perdida de cosecha."""
        ...

    def forecast_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """7.4: Holt-Winters para proyeccion tendencial."""
        ...

    def get_model_metrics(self) -> dict[str, Any]:
        """Retorna metricas consolidadas de todos los modelos."""
        ...
'''

# ═══════════════════════════════════════════════════════════
# core/ports/outbound/__init__.py
# ═══════════════════════════════════════════════════════════
OUTBOUND_INIT = '''"""
Puertos de SALIDA (outbound): definen lo que el nucleo de dominio
necesita del mundo exterior (persistencia, descarga, serializacion).

Los adaptadores de infraestructura (adapters/) implementan estos
protocolos. El nucleo solo conoce los contratos, no las implementaciones.
"""
from core.ports.outbound.storage_port import StoragePort
from core.ports.outbound.downloader_port import DownloaderPort
from core.ports.outbound.model_registry_port import ModelRegistryPort

__all__ = [
    "StoragePort",
    "DownloaderPort",
    "ModelRegistryPort",
]
'''

# ═══════════════════════════════════════════════════════════
# core/ports/outbound/storage_port.py
# ═══════════════════════════════════════════════════════════
STORAGE_PORT = '''"""
Puerto de salida para persistencia de archivos.

Define el contrato para leer/escribir archivos CSV, Excel y JSON.
Los adaptadores adapters/storage/ implementan este protocolo.

Este puerto es consumido por:
- Todos los pasos del pipeline (para cargar/guardar datos)
- El modulo de auditoria (para guardar reportes)
- El modulo de analytics (para exportar artefactos)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import pandas as pd


class StoragePort(Protocol):
    """Contrato para operaciones de lectura/escritura de archivos."""

    def read_csv(self, path: Path) -> pd.DataFrame:
        """
        Lee un archivo CSV y retorna un DataFrame.

        Args:
            path: Ruta al archivo CSV.

        Returns:
            DataFrame con los datos del CSV.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        ...

    def write_csv(
        self,
        df: pd.DataFrame,
        path: Path,
        encoding: str = "utf-8-sig",
        index: bool = False,
    ) -> None:
        """
        Escribe un DataFrame como CSV.

        Args:
            df: DataFrame a guardar.
            path: Ruta de destino.
            encoding: Codificacion (default utf-8-sig para Excel).
            index: Si incluir el indice (default False).
        """
        ...

    def read_excel(
        self,
        path: Path,
        sheet_name: str,
        skiprows: int = 0,
    ) -> pd.DataFrame:
        """
        Lee un archivo Excel (.xlsx) y retorna un DataFrame.

        Args:
            path: Ruta al archivo Excel.
            sheet_name: Nombre de la hoja.
            skiprows: Filas a saltar antes del header.

        Returns:
            DataFrame con los datos del Excel.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
            ValueError: Si la hoja no existe.
        """
        ...

    def read_json(self, path: Path) -> dict[str, Any]:
        """Lee un archivo JSON y retorna un diccionario."""
        ...

    def write_json(
        self,
        data: dict[str, Any],
        path: Path,
        indent: int = 2,
    ) -> None:
        """Escribe un diccionario como JSON."""
        ...

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo existe."""
        ...

    def file_size(self, path: Path) -> int:
        """Retorna el tamano del archivo en bytes."""
        ...
'''

# ═══════════════════════════════════════════════════════════
# core/ports/outbound/downloader_port.py
# ═══════════════════════════════════════════════════════════
DOWNLOADER_PORT = '''"""
Puerto de salida para descarga de datos de UPRA.

Define el contrato para descargar las bases EVA desde el portal
de la UPRA. El adaptador adapters/downloader/upra_downloader.py
implementa este protocolo usando Selenium.

Este puerto es consumido por:
- El script scripts/download_data.py
- La pagina de Configuracion de Streamlit (Fase 5)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class DownloaderPort(Protocol):
    """Contrato para descarga de archivos desde fuente externa."""

    def download(
        self,
        file_key: str,
        force: bool = False,
    ) -> Path:
        """
        Descarga un archivo identificado por file_key.

        Args:
            file_key: Identificador del archivo ("agricola", "pecuario").
            force: Si True, re-descarga aunque el checksum sea igual.

        Returns:
            Ruta local al archivo descargado.

        Raises:
            DownloaderError: Si la descarga falla tras todos los reintentos.
        """
        ...

    def verify_checksum(self, path: Path) -> bool:
        """
        Verifica que el archivo descargado es valido (magic bytes Excel).

        Args:
            path: Ruta al archivo descargado.

        Returns:
            True si el archivo tiene firma Excel valida.
        """
        ...

    def get_download_status(self) -> dict[str, Any]:
        """
        Retorna el estado de las descargas (para mostrar en UI).

        Returns:
            Dict con estado de cada archivo: exitoso, tamano, checksum, etc.
        """
        ...
'''

# ═══════════════════════════════════════════════════════════
# core/ports/outbound/model_registry_port.py
# ═══════════════════════════════════════════════════════════
MODEL_REGISTRY_PORT = '''"""
Puerto de salida para persistencia de modelos ML.

Define el contrato para guardar/cargar modelos entrenados.
El adaptador adapters/ml_registry/joblib_registry.py implementa
este protocolo usando joblib.

Este puerto resuelve el problema identificado en Fase 0:
los notebooks originales entrenaban modelos pero NO los persistian,
obligando a re-entrenar en cada ejecucion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class ModelRegistryPort(Protocol):
    """Contrato para persistencia de modelos ML."""

    def save_model(self, model: Any, name: str) -> Path:
        """
        Serializa y guarda un modelo entrenado.

        Args:
            model: Objeto del modelo (ej: RandomForestRegressor).
            name: Nombre unico del modelo (ej: "rf_regresion_v1").

        Returns:
            Ruta donde se guardo el modelo.

        Raises:
            ModelTrainingError: Si la serializacion falla.
        """
        ...

    def load_model(self, name: str) -> Any:
        """
        Carga un modelo previamente guardado.

        Args:
            name: Nombre unico del modelo.

        Returns:
            Objeto del modelo deserializado.

        Raises:
            FileNotFoundError: Si el modelo no existe.
        """
        ...

    def model_exists(self, name: str) -> bool:
        """Verifica si un modelo existe en el registro."""
        ...

    def list_models(self) -> list[str]:
        """Lista todos los modelos disponibles en el registro."""
        ...
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos corregidos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "core/ports/inbound/__init__.py": INBOUND_INIT,
        "core/ports/inbound/data_loader_port.py": DATA_LOADER_PORT,
        "core/ports/inbound/audit_port.py": AUDIT_PORT,
        "core/ports/inbound/analytics_port.py": ANALYTICS_PORT,
        "core/ports/inbound/diagnostics_port.py": DIAGNOSTICS_PORT,
        "core/ports/inbound/ml_port.py": ML_PORT,
        "core/ports/outbound/__init__.py": OUTBOUND_INIT,
        "core/ports/outbound/storage_port.py": STORAGE_PORT,
        "core/ports/outbound/downloader_port.py": DOWNLOADER_PORT,
        "core/ports/outbound/model_registry_port.py": MODEL_REGISTRY_PORT,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\nCorreccion completada. {creados} archivos recreados.")
    print('Ejecuta: python -c "from core.ports.inbound import AnalyticsPort; print(\'OK\')"')