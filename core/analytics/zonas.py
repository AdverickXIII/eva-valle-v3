"""Zonificacion oficial del Valle del Cauca (POTD / Ordenanza 513 de 2019)."""
from __future__ import annotations

import pandas as pd

ZONAS = {
    "Norte": [
        "Alcalá", "Alcala", "Ansermanuevo", "Argelia", "Bolívar", "Bolivar",
        "Cartago", "El Águila", "El Aguila", "El Cairo", "El Dovio",
        "La Unión", "La Union", "La Victoria", "Obando", "Roldanillo",
        "Toro", "Ulloa", "Versalles", "Zarzal"],
    "Centro": [
        "Andalucía", "Andalucia", "Guadalajara de Buga", "Buga", "Bugalagrande",
        "Calima", "Darien", "Ginebra", "Guacarí", "Guacari", "Restrepo",
        "Riofrío", "Riofrio", "San Pedro", "Trujillo", "Tuluá", "Tulua",
        "Yotoco", "Sevilla", "Caicedonia"],
    "Sur": [
        "Cali", "Santiago de Cali", "Candelaria", "Dagua", "El Cerrito",
        "Florida", "Jamundí", "Jamundi", "La Cumbre", "Palmira", "Pradera",
        "Vijes", "Yumbo"],
    "Pacífico": ["Buenaventura"],
}


def asignar_zona(municipio: str) -> str:
    m = str(municipio).strip()
    for zona, lista in ZONAS.items():
        if m in lista:
            return zona
    return "Sin zona"


def gini(values) -> float:
    v = sorted(float(x) for x in values if x > 0)
    n = len(v)
    if n == 0 or sum(v) == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(v))
    return (2 * cum) / (n * sum(v)) - (n + 1) / n


def indicadores_por_zona(df: pd.DataFrame, excluye_cana: bool = False) -> pd.DataFrame:
    if excluye_cana:
        df = df[df["cultivo"] != "Caña"]
    filas = []
    total = df["produccion_t"].sum()
    for zona in ZONAS.keys():
        sub = df[df["zona"] == zona]
        if sub.empty:
            continue
        prod = sub["produccion_t"].sum()
        sem = sub["area_sembrada_ha"].sum()
        cos = sub["area_cosechada_ha"].sum()
        filas.append({
            "zona": zona,
            "municipios": sub["municipio"].nunique(),
            "produccion_t": prod,
            "area_sembrada_ha": sem,
            "area_cosechada_ha": cos,
            "rendimiento_t_ha": prod / cos if cos else 0,
            "aprovechamiento_pct": (cos / sem * 100) if sem else 0,
            "share_dept_pct": prod / total * 100 if total else 0,
            "gini_municipios": gini(sub.groupby("municipio")["produccion_t"].sum().values),
            "gini_cultivos": gini(sub.groupby("cultivo")["produccion_t"].sum().values),
        })
    return pd.DataFrame(filas).set_index("zona")
