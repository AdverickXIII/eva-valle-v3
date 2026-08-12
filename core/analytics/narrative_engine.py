"""Motor narrativo: genera insights en formato DATO/INTERPRETACION/IMPLICACION
y la 'frase de la agricultura' como cierre memorable.
"""
from __future__ import annotations

import pandas as pd
from core.analytics.executive import executive_summary
from core.analytics.pareto import conc_metrics, territorial
from core.analytics.informe_indicators import idam, brechas
from core.analytics.strategic_matrices import matriz_cultivos, matriz_municipios


def generar_insights(df: pd.DataFrame) -> list[dict]:
    """Genera 10 insights automaticos en formato DATO/INTERPRETACION/IMPLICACION."""
    s = executive_summary(df)
    cc = conc_metrics(df, False)
    sc = conc_metrics(df, True)
    ter = territorial(df)
    bg = brechas(df)
    mc = matriz_cultivos(df)
    mm = matriz_municipios(df)
    
    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    ultimo, anterior = anos[-1], anos[-2]
    p_ult = df[df["ano"] == ultimo]["produccion_t"].sum()
    p_ant = df[df["ano"] == anterior]["produccion_t"].sum()
    var_pct = ((p_ult - p_ant) / p_ant * 100) if p_ant else 0
    
    insights = []
    
    # 1. Concentracion productiva
    insights.append({
        "dato": f"La cana concentra el {cc['top1_pct']:.1f}% de la produccion departamental.",
        "interpretacion": "El HHI con cana es {hhi:,} (monocultivo extremo), pero sin cana cae a {hhi_sin:,}.".format(
            hhi=cc['hhi'], hhi_sin=sc['hhi']),
        "implicacion": "La economia agricola no-canera es diversificada ({n} cultivos explican el 80%).".format(
            n=sc['n80']),
    })
    
    # 2. Concentracion territorial
    insights.append({
        "dato": f"El Gini territorial es {ter['gini']:.2f} (alta concentracion espacial).",
        "interpretacion": f"{ter['top']} lidera con el {ter['top_pct']:.1f}% de la produccion.",
        "implicacion": "La produccion se concentra en pocos municipios; se requiere focalizar inversion.",
    })
    
    # 3. Crecimiento interanual
    insights.append({
        "dato": f"La produccion crecio {var_pct:+.1f}% entre {anterior} y {ultimo}.",
        "interpretacion": f"Paso de {p_ant:,.0f} a {p_ult:,.0f} toneladas.",
        "implicacion": "El crecimiento es modesto (+{:.1f}% anual promedio).".format(var_pct / (ultimo - anterior))
        if var_pct > 0 else "La produccion se contrajo, requiriendo analisis de causas.",
    })
    
    # 4. Cultivos motores
    motores = mc[mc["cuadrante"] == "Motor"].head(3)
    if not motores.empty:
        nombres = ", ".join(motores["cultivo"].tolist())
        insights.append({
            "dato": f"Cultivos motores: {nombres}.",
            "interpretacion": "Alta participacion y alto crecimiento (CAGR positivo).",
            "implicacion": "Son los motores del crecimiento agricola; priorizar apoyo.",
        })
    
    # 5. Cultivos consolidados
    consol = mc[mc["cuadrante"] == "Consolidado"].head(3)
    if not consol.empty:
        nombres = ", ".join(consol["cultivo"].tolist())
        insights.append({
            "dato": f"Cultivos consolidados: {nombres}.",
            "interpretacion": "Alta participacion pero crecimiento bajo o negativo.",
            "implicacion": "Requieren estrategias de renovacion o diversificacion.",
        })
    
    # 6. Cultivos emergentes
    emerg = mc[mc["cuadrante"] == "Emergente"].head(3)
    if not emerg.empty:
        nombres = ", ".join(emerg["cultivo"].tolist())
        insights.append({
            "dato": f"Cultivos emergentes: {nombres}.",
            "interpretacion": "Baja participacion pero alto crecimiento.",
            "implicacion": "Oportunidad de inversion para escalar produccion.",
        })
    
    # 7. Municipios motores
    mun_motores = mm[mm["cuadrante"] == "Motores"].head(3)
    if not mun_motores.empty:
        nombres = ", ".join(mun_motores["municipio"].tolist())
        insights.append({
            "dato": f"Municipios motores: {nombres}.",
            "interpretacion": "Alta produccion y alta productividad.",
            "implicacion": "Son los pilares de la produccion departamental.",
        })
    
    # 8. Municipios de mejora
    mun_mejora = mm[mm["cuadrante"] == "Mejora"]
    if not mun_mejora.empty:
        nombres = ", ".join(mun_mejora["municipio"].tolist())
        insights.append({
            "dato": f"Municipios de mejora: {nombres}.",
            "interpretacion": "Alta produccion pero baja productividad.",
            "implicacion": "Requieren asistencia tecnica para mejorar rendimientos.",
        })
    
    # 9. Brecha territorial
    if bg and bg.get("ratio_p90_p10"):
        insights.append({
            "dato": f"La brecha P90/P10 es {bg['ratio_p90_p10']:.1f}x.",
            "interpretacion": "El municipio en el percentil 90 produce {:.1f} veces mas que el del percentil 10.".format(
                bg['ratio_p90_p10']),
            "implicacion": "Existe alta desigualdad territorial en la produccion.",
        })
    
    # 10. Diversificacion
    sin_cana_hhi = sc['hhi']
    if sin_cana_hhi < 1500:
        insights.append({
            "dato": f"Sin cana, el HHI es {sin_cana_hhi:,} (diversificacion moderada).",
            "interpretacion": "La economia no-canera tiene {n} cultivos relevantes.".format(n=sc['n80']),
            "implicacion": "Hay base solida para diversificar hacia cultivos de mayor valor.",
        })
    
    return insights[:10]


def frase_de_la_agricultura(df: pd.DataFrame) -> str:
    """Genera la 'frase de la agricultura' como cierre memorable."""
    s = executive_summary(df)
    anos = sorted(int(a) for a in df["ano"].dropna().unique())
    ini, fin = anos[0], anos[-1]
    p_ini = df[df["ano"] == ini]["produccion_t"].sum()
    p_fin = df[df["ano"] == fin]["produccion_t"].sum()
    crecimiento_pct = ((p_fin - p_ini) / p_ini * 100) if p_ini else 0
    
    ter = territorial(df)
    cc = conc_metrics(df, False)
    sc = conc_metrics(df, True)
    mc = matriz_cultivos(df)
    
    motores = mc[mc["cuadrante"] == "Motor"]
    emergentes = mc[mc["cuadrante"] == "Emergente"]
    
    # Determinar caracterizacion
    if crecimiento_pct > 10:
        caracterizacion = "un crecimiento solido"
    elif crecimiento_pct > 0:
        caracterizacion = "un crecimiento modesto"
    else:
        caracterizacion = "una contraccion"
    
    # Determinar que la caracteriza
    if cc['top1_pct'] > 90:
        caracterizada_por = "la dominancia extrema de la cana de azucar"
    elif ter['gini'] > 0.6:
        caracterizada_por = "alta concentracion territorial"
    else:
        caracterizada_por = "diversificacion productiva moderada"
    
    # Determinar estructura
    if cc['hhi'] > 2500:
        estructura = "alta concentracion productiva (monocultivo)"
    else:
        estructura = "diversificacion moderada"
    
    # Determinar oportunidades
    if not emergentes.empty:
        nombres = ", ".join(emergentes.head(2)["cultivo"].tolist())
        oportunidades = f"cultivos emergentes como {nombres}"
    else:
        oportunidades = "municipios con potencial de mejora"
    
    frase = (
        f"Entre {ini} y {fin}, la agricultura del Valle del Cauca experimento {caracterizacion} "
        f"(+{crecimiento_pct:.1f}%), caracterizada por {caracterizada_por}. "
        f"Sin embargo, la estructura productiva mantiene {estructura}, "
        f"mientras que las principales oportunidades se concentran en {oportunidades}."
    )
    
    return frase


def resumen_ejecutivo_narrativo(df: pd.DataFrame) -> dict:
    """Genera el resumen ejecutivo narrativo completo."""
    insights = generar_insights(df)
    frase = frase_de_la_agricultura(df)
    
    return {
        "insights": insights,
        "frase_cierre": frase,
        "total_insights": len(insights),
    }
