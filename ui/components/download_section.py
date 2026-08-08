"""Botones de descarga de artefactos."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


def render_download_button(
    df: pd.DataFrame,
    filename: str,
    label: str = "\U0001F4E5 Descargar CSV",
    key: str | None = None,
) -> None:
    """
    Renderiza un boton de descarga de DataFrame como CSV.

    Args:
        df: DataFrame a descargar.
        filename: Nombre del archivo de salida.
        label: Texto del boton.
        key: Key unica del widget.
    """
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv",
        key=key or f"download_{filename}",
    )


def render_file_download(
    filepath: Path,
    label: str | None = None,
) -> None:
    """
    Renderiza un boton de descarga de un archivo existente.

    Args:
        filepath: Ruta al archivo.
        label: Texto del boton. Si None, usa el nombre del archivo.
    """
    if not filepath.exists():
        st.warning(f"Archivo no disponible: {filepath.name}")
        return

    with open(filepath, "rb") as f:
        data = f.read()

    st.download_button(
        label=label or f"\U0001F4E5 {filepath.name}",
        data=data,
        file_name=filepath.name,
        key=f"download_file_{filepath.name}",
    )
