"""Tests de target encoding (previene data leakage)."""
import pandas as pd

from core.ml.target_encoding import apply_target_encoding, fit_target_encoding


def test_fit_calcula_medias_de_train():
    train = pd.DataFrame({
        "municipio": ["M1", "M1", "M2"],
        "rendimiento_t_ha": [10.0, 20.0, 30.0],
    })
    maps = fit_target_encoding(train)
    assert maps["municipio"]["M1"] == 15.0
    assert maps["municipio"]["M2"] == 30.0


def test_apply_usa_medias_de_train_y_rellena_no_vistos():
    """Un municipio no visto en train se rellena con la media global (no con su propia media)."""
    train = pd.DataFrame({
        "municipio": ["M1", "M1"],
        "rendimiento_t_ha": [10.0, 20.0],
    })
    maps = fit_target_encoding(train)

    test = pd.DataFrame({"municipio": ["M1", "M3"]})
    res = apply_target_encoding(test, maps)

    assert res["target_enc_municipio"].iloc[0] == 15.0   # visto en train
    assert res["target_enc_municipio"].iloc[1] == 15.0   # no visto -> media global
    assert not res["target_enc_municipio"].isna().any()
