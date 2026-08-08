"""
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
        magic_bytes = {b"PK\x03\x04", b"\xd0\xcf\x11\xe0"}
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
