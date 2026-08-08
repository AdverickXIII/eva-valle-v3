"""Tests de analisis espacial."""
import pandas as pd

from core.analytics.spatial import calculate_shannon_diversity


def test_shannon_retorna_dataframe():
    df = pd.DataFrame({
        "municipio": ["M1", "M2"],
        "area_sembrada_ha": [10.0, 20.0],
    })
    res = calculate_shannon_diversity(df)
    assert "shannon_wiener" in res.columns
    assert len(res) == 2
