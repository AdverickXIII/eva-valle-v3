"""
Setup script: genera los 9 archivos de adaptadores (implementaciones de puertos).
Ejecutar una sola vez: python scripts/setup_adapters.py
"""
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ARCHIVO 1: adapters/__init__.py
# ═══════════════════════════════════════════════════════════
ADAPTERS_INIT = '''"""
Adaptadores de infraestructura del proyecto eva-valle-v3.0.

Los adaptadores implementan los puertos definidos en core/ports/.
El nucleo de dominio NUNCA importa de este paquete directamente;
solo conoce los puertos (contratos).

Arquitectura Hexagonal:
    - adapters/storage/      → Implementa StoragePort (CSV, Excel, JSON)
    - adapters/downloader/   → Implementa DownloaderPort (Selenium UPRA)
    - adapters/ml_registry/  → Implementa ModelRegistryPort (joblib)
"""
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 2: adapters/storage/__init__.py
# ═══════════════════════════════════════════════════════════
STORAGE_INIT = '''"""
Adaptadores de persistencia de archivos.
Implementan el puerto core.ports.outbound.StoragePort.
"""
from adapters.storage.csv_storage import CsvStorage
from adapters.storage.excel_storage import ExcelStorage
from adapters.storage.json_storage import JsonStorage

__all__ = ["CsvStorage", "ExcelStorage", "JsonStorage"]
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 3: adapters/storage/csv_storage.py
# ═══════════════════════════════════════════════════════════
CSV_STORAGE = '''"""
Adaptador de almacenamiento CSV.
Implementa el puerto StoragePort para archivos CSV.

Resuelve problemas del pipeline original:
- Validacion de existencia antes de leer
- Encoding consistente (utf-8-sig para compatibilidad con Excel)
- Logging centralizado
- Excepciones personalizadas con mensajes claros
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.exceptions import DatasetNotFoundError
from core.logging import get_logger

log = get_logger("adapters.storage.csv")


class CsvStorage:
    """Adaptador para lectura/escritura de archivos CSV."""

    def read_csv(
        self,
        path: Path,
        encoding: str = "utf-8-sig",
        low_memory: bool = False,
    ) -> pd.DataFrame:
        """
        Lee un archivo CSV y retorna un DataFrame.

        Args:
            path: Ruta al archivo CSV.
            encoding: Codificacion del archivo (default utf-8-sig).
            low_memory: Si False, pandas infiere tipos de forma consistente.

        Returns:
            DataFrame con los datos del CSV.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        if not path.exists():
            raise DatasetNotFoundError(
                path,
                "Ejecuta el paso anterior del pipeline primero.",
            )

        log.info("Leyendo CSV: %s", path.name)
        df = pd.read_csv(path, encoding=encoding, low_memory=low_memory)
        log.info(
            "CSV cargado: %s (%d filas x %d columnas)",
            path.name,
            len(df),
            len(df.columns),
        )
        return df

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
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=index, encoding=encoding)
        log.info("CSV guardado: %s (%d filas)", path.name, len(df))

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo CSV existe."""
        return path.exists()

    def file_size(self, path: Path) -> int:
        """Retorna el tamano del archivo en bytes."""
        if not path.exists():
            return 0
        return path.stat().st_size
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 4: adapters/storage/excel_storage.py
# ═══════════════════════════════════════════════════════════
EXCEL_STORAGE = '''"""
Adaptador de almacenamiento Excel.
Implementa el puerto StoragePort para archivos .xlsx.

Resuelve problemas del pipeline original:
- Validacion de tamano minimo antes de leer
- Validacion de magic bytes (firma Excel)
- Deteccion automatica de fila de header
- Excepciones personalizadas
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.constants import MIN_FILE_BYTES
from core.exceptions import DatasetNotFoundError
from core.logging import get_logger

log = get_logger("adapters.storage.excel")

# Firmas binarias de archivos Excel
_EXCEL_MAGIC_BYTES = {
    b"PK\\x03\\x04": ".xlsx",   # ZIP (Office Open XML)
    b"\\xd0\\xcf\\x11\\xe0": ".xls",  # OLE2 (Excel 97-2003)
}


class ExcelStorage:
    """Adaptador para lectura de archivos Excel (.xlsx/.xls)."""

    def read_excel(
        self,
        path: Path,
        sheet_name: str,
        skiprows: int = 0,
        dtype: type | None = str,
    ) -> pd.DataFrame:
        """
        Lee un archivo Excel y retorna un DataFrame.

        Args:
            path: Ruta al archivo Excel.
            sheet_name: Nombre de la hoja a leer.
            skiprows: Filas a saltar antes del header.
            dtype: Tipo de dato para todas las columnas (default str).

        Returns:
            DataFrame con los datos del Excel.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
            ValueError: Si el archivo es demasiado pequeno o no es Excel valido.
        """
        if not path.exists():
            raise DatasetNotFoundError(
                path,
                "Ejecuta el Downloader (Paso 0) primero.",
            )

        # Validar tamano minimo
        size = path.stat().st_size
        if size < MIN_FILE_BYTES:
            raise ValueError(
                f"Archivo sospechosamente pequeno: {size:,} bytes "
                f"(minimo: {MIN_FILE_BYTES:,}). Posible descarga truncada."
            )

        # Validar magic bytes
        if not self._is_valid_excel(path):
            raise ValueError(
                f"El archivo {path.name} no tiene firma Excel valida."
            )

        log.info(
            "Leyendo Excel: %s | Hoja: %s | skiprows=%d",
            path.name,
            sheet_name,
            skiprows,
        )
        df = pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl",
            skiprows=skiprows,
            header=0,
            dtype=dtype,
        )
        log.info(
            "Excel cargado: %s (%d filas x %d columnas)",
            path.name,
            len(df),
            len(df.columns),
        )
        return df

    def detect_header_row(
        self,
        path: Path,
        sheet_name: str,
        search_term: str = "departamento",
        max_scan: int = 15,
    ) -> int:
        """
        Detecta automaticamente la fila del header buscando un termino.

        Args:
            path: Ruta al archivo Excel.
            sheet_name: Nombre de la hoja.
            search_term: Termino a buscar en las filas.
            max_scan: Maximo de filas a escanear.

        Returns:
            Indice (base 0) de la fila del header.

        Raises:
            ValueError: Si no se encuentra el header.
        """
        df_scan = pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl",
            nrows=max_scan,
            header=None,
        )
        for idx, row in df_scan.iterrows():
            valores = [
                str(v).strip().lower()
                for v in row.values
                if str(v) != "nan"
            ]
            if any(search_term in v for v in valores):
                log.info("Header detectado en fila %d (base 0).", idx)
                return idx

        raise ValueError(
            f"No se encontro '{search_term}' en las primeras "
            f"{max_scan} filas. El archivo pudo haber cambiado de formato."
        )

    def get_sheet_names(self, path: Path) -> list[str]:
        """Retorna los nombres de todas las hojas del archivo Excel."""
        xl = pd.ExcelFile(path, engine="openpyxl")
        return xl.sheet_names

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo Excel existe."""
        return path.exists()

    def file_size(self, path: Path) -> int:
        """Retorna el tamano del archivo en bytes."""
        if not path.exists():
            return 0
        return path.stat().st_size

    @staticmethod
    def _is_valid_excel(path: Path) -> bool:
        """Verifica que el archivo tenga firma Excel valida (magic bytes)."""
        if not path.exists() or path.stat().st_size == 0:
            return False
        with open(path, "rb") as f:
            header = f.read(8)
        return any(header.startswith(magic) for magic in _EXCEL_MAGIC_BYTES)
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 5: adapters/storage/json_storage.py
# ═══════════════════════════════════════════════════════════
JSON_STORAGE = '''"""
Adaptador de almacenamiento JSON.
Implementa el puerto StoragePort para archivos JSON.

Usado para:
- Mapa conceptual (Paso 3)
- Manifest de checksums (Paso 0)
- Configuraciones exportadas
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.exceptions import DatasetNotFoundError
from core.logging import get_logger

log = get_logger("adapters.storage.json")


class JsonStorage:
    """Adaptador para lectura/escritura de archivos JSON."""

    def read_json(self, path: Path) -> dict[str, Any]:
        """
        Lee un archivo JSON y retorna un diccionario.

        Args:
            path: Ruta al archivo JSON.

        Returns:
            Diccionario con los datos del JSON.

        Raises:
            DatasetNotFoundError: Si el archivo no existe.
        """
        if not path.exists():
            raise DatasetNotFoundError(path)

        log.info("Leyendo JSON: %s", path.name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.info("JSON cargado: %s", path.name)
        return data

    def write_json(
        self,
        data: dict[str, Any],
        path: Path,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> None:
        """
        Escribe un diccionario como JSON.

        Args:
            data: Diccionario a guardar.
            path: Ruta de destino.
            indent: Nivel de indentacion (default 2).
            ensure_ascii: Si False, permite caracteres Unicode (tildes).
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        log.info("JSON guardado: %s", path.name)

    def exists(self, path: Path) -> bool:
        """Verifica si un archivo JSON existe."""
        return path.exists()

    def file_size(self, path: Path) -> int:
        """Retorna el tamano del archivo en bytes."""
        if not path.exists():
            return 0
        return path.stat().st_size
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 6: adapters/downloader/__init__.py
# ═══════════════════════════════════════════════════════════
DOWNLOADER_INIT = '''"""
Adaptador de descarga de datos del portal UPRA.
Implementa el puerto core.ports.outbound.DownloaderPort.
"""
from adapters.downloader.upra_downloader import UpraDownloader

__all__ = ["UpraDownloader"]
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 7: adapters/downloader/upra_downloader.py
# ═══════════════════════════════════════════════════════════
DOWNLOADER = '''"""
Adaptador de descarga del portal UPRA usando Selenium.
Implementa el puerto DownloaderPort.

Migrado del Notebook 1 (Downloader v3.2) con las siguientes mejoras:
- Sin subprocess para instalacion de paquetes
- Logging centralizado (no duplicado)
- Configuracion desde config.settings (no hardcodeada)
- Excepciones personalizadas (DownloaderError)
- Type hints completos
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings
from core.exceptions import DownloaderError
from core.logging import get_logger

log = get_logger("adapters.downloader.upra")

# ── Constantes del adaptador ─────────────────────────────────
_DOWNLOAD_CHUNK = 8192
_WAIT_TIMEOUT = 20

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://upra.gov.co/",
}

_TARGET_FILES: dict[str, dict[str, str]] = {
    "agricola": {
        "tab_keyword": "agricola",
        "file_keyword": "base agr",
        "output_name": "base_agricola_2024",
    },
    "pecuario": {
        "tab_keyword": "pecuario",
        "file_keyword": "base pecuaria",
        "output_name": "base_pecuaria_evas_2019_2024",
    },
}


@dataclass
class DownloadResult:
    """Resultado de una descarga individual."""

    clave: str
    exitoso: bool = False
    saltado: bool = False
    url_descarga: Optional[str] = None
    filepath: Optional[str] = None
    tamanio_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    valido_excel: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


class UpraDownloader:
    """
    Descarga las bases Agricola y Pecuaria del portal EVA de la UPRA.
    Implementa el puerto DownloaderPort.
    """

    def __init__(self, force_redownload: bool = False) -> None:
        self._force = force_redownload
        self._session = self._create_http_session()
        self._manifest_path = (
            settings.OUTPUTS_TABLES_PATH / "00_manifest_checksums.json"
        )
        settings.DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
        settings.OUTPUTS_TABLES_PATH.mkdir(parents=True, exist_ok=True)

    # ── DownloaderPort: download ────────────────────────────────
    def download(self, file_key: str, force: bool = False) -> Path:
        """
        Descarga un archivo identificado por file_key.

        Args:
            file_key: Identificador del archivo ("agricola" o "pecuario").
            force: Si True, re-descarga aunque el checksum sea igual.

        Returns:
            Ruta local al archivo descargado.

        Raises:
            DownloaderError: Si la descarga falla tras todos los reintentos.
        """
        if file_key not in _TARGET_FILES:
            raise DownloaderError(
                file_key,
                f"Clave desconocida. Validas: {list(_TARGET_FILES.keys())}",
            )

        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        from webdriver_manager.chrome import ChromeDriverManager

        cfg = _TARGET_FILES[file_key]
        driver = self._init_driver(webdriver, Options, Service, ChromeDriverManager)

        try:
            self._navigate(driver, webdriver, By, EC, WebDriverWait, settings.UPRA_BASE_URL)
            self._expand_tab(driver, By, cfg["tab_keyword"])
            url = self._extract_url(driver, cfg["file_keyword"])
            if not url:
                raise DownloaderError(file_key, "No se encontro enlace de descarga")

            filepath = self._download_file(url, cfg["output_name"])
            if not filepath:
                raise DownloaderError(file_key, "La descarga no produjo archivo valido", url)

            return filepath
        finally:
            driver.quit()
            log.info("WebDriver cerrado.")

    # ── DownloaderPort: verify_checksum ─────────────────────────
    def verify_checksum(self, path: Path) -> bool:
        """Verifica que el archivo tenga firma Excel valida."""
        if not path.exists() or path.stat().st_size == 0:
            return False
        magic_bytes = {b"PK\\x03\\x04", b"\\xd0\\xcf\\x11\\xe0"}
        with open(path, "rb") as f:
            header = f.read(8)
        return any(header.startswith(m) for m in magic_bytes)

    # ── DownloaderPort: get_download_status ─────────────────────
    def get_download_status(self) -> dict[str, Any]:
        """Retorna el estado de las descargas."""
        manifest = self._load_manifest()
        status = {}
        for key in _TARGET_FILES:
            filepath = settings.DATA_RAW_PATH / f"{_TARGET_FILES[key]['output_name']}.xlsx"
            status[key] = {
                "existe": filepath.exists(),
                "checksum_manifest": manifest.get(key),
                "tamano": filepath.stat().st_size if filepath.exists() else 0,
            }
        return status

    # ── Metodos privados ────────────────────────────────────────
    def _create_http_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(_HTTP_HEADERS)
        retries = Retry(
            total=settings.DOWNLOAD_RETRIES,
            backoff_factor=1.5,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.mount("http://", HTTPAdapter(max_retries=retries))
        return session

    def _init_driver(self, webdriver, Options, Service, ChromeDriverManager):
        options = Options()
        if settings.HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"user-agent={_HTTP_HEADERS['User-Agent']}")

        for intento in range(1, 4):
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                driver.set_page_load_timeout(settings.DOWNLOAD_TIMEOUT)
                log.info("WebDriver inicializado (intento %d).", intento)
                return driver
            except Exception as e:
                log.warning("Fallo WebDriver (intento %d/3): %s", intento, e)
                time.sleep(2 * intento)

        # Fallback: chromedriver del sistema
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(settings.DOWNLOAD_TIMEOUT)
            log.info("WebDriver inicializado (fallback).")
            return driver
        except Exception as e:
            raise DownloaderError("webdriver", f"No se pudo iniciar: {e}")

    def _navigate(self, driver, webdriver, By, EC, WebDriverWait, url: str) -> None:
        log.info("Navegando a: %s", url)
        driver.get(url)
        WebDriverWait(driver, _WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        log.info("Pagina cargada: %s", driver.title)

    def _expand_tab(self, driver, By, tab_keyword: str) -> bool:
        kw = tab_keyword.lower()
        xpaths = [
            f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw}')]",
            f"//h3[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw}')]",
        ]
        for xpath in xpaths:
            try:
                elementos = driver.find_elements(By.XPATH, xpath)
                for el in elementos:
                    text = el.text.strip().lower()
                    if kw in text and len(text) < 80:
                        driver.execute_script("arguments[0].click();", el)
                        time.sleep(1)
                        log.info("Pestana '%s' expandida.", tab_keyword)
                        return True
            except Exception:
                continue
        raise DownloaderError(tab_keyword, f"No se encontro la pestana '{tab_keyword}'")

    def _extract_url(self, driver, file_keyword: str) -> Optional[str]:
        soup = BeautifulSoup(driver.page_source, "lxml")
        base_domain = "https://upra.gov.co"
        for a in soup.find_all("a", href=True):
            texto = a.get_text(strip=True).lower()
            href = a["href"]
            if file_keyword.lower() in texto or file_keyword.lower() in href.lower():
                url = href if href.startswith("http") else base_domain + href
                if ".xlsx" in url.lower() or ".xls" in url.lower():
                    return url
        return None

    def _download_file(self, url: str, nombre_base: str) -> Optional[Path]:
        for intento in range(1, settings.DOWNLOAD_RETRIES + 1):
            filepath = settings.DATA_RAW_PATH / f"{nombre_base}.xlsx"
            try:
                response = self._session.get(url, stream=True, timeout=settings.DOWNLOAD_TIMEOUT)
                if response.status_code != 200:
                    raise DownloaderError(nombre_base, f"HTTP {response.status_code}", url)

                content_length = int(response.headers.get("Content-Length", 0) or 0)
                bytes_escritos = 0

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=_DOWNLOAD_CHUNK):
                        if chunk:
                            f.write(chunk)
                            bytes_escritos += len(chunk)

                if content_length and bytes_escritos < content_length:
                    raise IOError(
                        f"Descarga incompleta: {bytes_escritos / 1024**2:.1f} MB "
                        f"de {content_length / 1024**2:.1f} MB esperados."
                    )

                log.info("Descarga completada: %s (%.1f MB)", filepath.name, bytes_escritos / 1024**2)
                return filepath

            except (requests.exceptions.RequestException, IOError) as e:
                if filepath.exists():
                    filepath.unlink()
                log.warning("Intento %d/%d fallo: %s", intento, settings.DOWNLOAD_RETRIES, e)
                if intento < settings.DOWNLOAD_RETRIES:
                    time.sleep(3 * intento)

        return None

    def _load_manifest(self) -> dict[str, str]:
        if self._manifest_path.exists():
            try:
                return json.loads(self._manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_manifest(self, manifest: dict[str, str]) -> None:
        self._manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 8: adapters/ml_registry/__init__.py
# ═══════════════════════════════════════════════════════════
ML_REGISTRY_INIT = '''"""
Adaptador de persistencia de modelos ML.
Implementa el puerto core.ports.outbound.ModelRegistryPort.
"""
from adapters.ml_registry.joblib_registry import JoblibModelRegistry

__all__ = ["JoblibModelRegistry"]
'''

# ═══════════════════════════════════════════════════════════
# ARCHIVO 9: adapters/ml_registry/joblib_registry.py
# ═══════════════════════════════════════════════════════════
JOBLIB_REGISTRY = '''"""
Adaptador de persistencia de modelos ML usando joblib.
Implementa el puerto ModelRegistryPort.

Resuelve el problema identificado en Fase 0:
los notebooks originales entrenaban modelos pero NO los persistian,
obligando a re-entrenar en cada ejecucion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from config.settings import settings
from core.exceptions import ModelTrainingError
from core.logging import get_logger

log = get_logger("adapters.ml_registry.joblib")


class JoblibModelRegistry:
    """Registro de modelos ML persistidos con joblib."""

    def __init__(self) -> None:
        settings.MODELS_PATH.mkdir(parents=True, exist_ok=True)

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
        path = settings.MODELS_PATH / f"{name}.joblib"
        try:
            joblib.dump(model, path)
            log.info("Modelo guardado: %s (%.1f KB)", name, path.stat().st_size / 1024)
            return path
        except Exception as e:
            raise ModelTrainingError(name, f"Fallo al serializar: {e}") from e

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
        path = settings.MODELS_PATH / f"{name}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {path}")
        log.info("Modelo cargado: %s", name)
        return joblib.load(path)

    def model_exists(self, name: str) -> bool:
        """Verifica si un modelo existe en el registro."""
        return (settings.MODELS_PATH / f"{name}.joblib").exists()

    def list_models(self) -> list[str]:
        """Lista todos los modelos disponibles en el registro."""
        return [
            p.stem
            for p in settings.MODELS_PATH.glob("*.joblib")
        ]
'''

# ═══════════════════════════════════════════════════════════
# EJECUCION: Crear todos los archivos
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    archivos = {
        "adapters/__init__.py": ADAPTERS_INIT,
        "adapters/storage/__init__.py": STORAGE_INIT,
        "adapters/storage/csv_storage.py": CSV_STORAGE,
        "adapters/storage/excel_storage.py": EXCEL_STORAGE,
        "adapters/storage/json_storage.py": JSON_STORAGE,
        "adapters/downloader/__init__.py": DOWNLOADER_INIT,
        "adapters/downloader/upra_downloader.py": DOWNLOADER,
        "adapters/ml_registry/__init__.py": ML_REGISTRY_INIT,
        "adapters/ml_registry/joblib_registry.py": JOBLIB_REGISTRY,
    }

    creados = 0
    for ruta, contenido in archivos.items():
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contenido, encoding="utf-8")
        print(f"[OK] {ruta}")
        creados += 1

    print(f"\n{creados} archivos de adaptadores creados.")
    print('Ejecuta: python -c "from adapters.storage import CsvStorage; print(\'OK\')"')