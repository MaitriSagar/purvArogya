import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from purvarogya.scoring import FLAG_CUTOFF, assess, percentile_of, risk_level, score_drivers

FEATURES = ["_bmi5", "_drnkwk2", "_smoker3", "_rfchol3", "income3", "genhlth", "_totinda",
            "menthlth", "physhlth", "bphigh6", "_ageg5yr", "_sex", "_educag"]


def make_data(n=3000):
    rng = np.random.default_rng(0)
    X = pd.DataFrame({
        "_bmi5": rng.normal(28, 6, n), "_drnkwk2": rng.exponential(2, n),
        "_smoker3": rng.integers(1, 5, n), "_rfchol3": rng.integers(1, 3, n),
        "income3": rng.integers(1, 12, n), "genhlth": rng.integers(1, 6, n),
        "_totinda": rng.integers(1, 3, n), "menthlth": rng.integers(0, 31, n),
        "physhlth": rng.integers(0, 31, n), "bphigh6": rng.integers(0, 3, n),
        "_ageg5yr": rng.integers(1, 14, n), "_sex": rng.integers(1, 3, n),
        "_educag": rng.integers(1, 5, n)})[FEATURES]
    # sicker answers (poor health, older, high blood pressure) -> more often positive
    risk = 0.6 * (X["genhlth"] - 3) + 0.3 * (X["_ageg5yr"] - 7) + 0.8 * X["bphigh6"]
    y = (rng.random(n) < 1 / (1 + np.exp(-(risk - 2)))).astype(int)
    return X, y


def make_model(X, y):
    scale_cols = [c for c in FEATURES if c not in ("_drnkwk2", "_smoker3")]
    prep = ColumnTransformer([
        ("drinks", Pipeline([("log", FunctionTransformer(np.log1p)), ("scale", StandardScaler())]), ["_drnkwk2"]),
        ("smoker", OneHotEncoder(handle_unknown="ignore"), ["_smoker3"]),
        ("scale", StandardScaler(), scale_cols)])
    return Pipeline([("prep", prep), ("lr", LogisticRegression(C=0.01, max_iter=1000,
                                                                class_weight="balanced"))]).fit(X, y)


def one_person(**changes):
    base = {"_bmi5": 27, "_drnkwk2": 1, "_smoker3": 4, "_rfchol3": 1, "income3": 7, "genhlth": 3,
            "_totinda": 1, "menthlth": 0, "physhlth": 0, "bphigh6": 0, "_ageg5yr": 7, "_sex": 1,
            "_educag": 3}
    base.update(changes)
    return pd.DataFrame([base])[FEATURES]


def test_percentile_is_between_0_and_99():
    saved = np.percentile(np.linspace(0, 1, 1000), np.arange(0, 101))
    assert percentile_of(-5, saved) == 0
    assert percentile_of(5, saved) == 99
    assert 48 <= percentile_of(0.5, saved) <= 51


def test_sicker_person_gets_higher_percentile_and_flag():
    X, y = make_data()
    model = make_model(X, y)
    saved = {"diabetes_target": np.percentile(model.predict_proba(X)[:, 1], np.arange(0, 101))}

    healthy = assess({"diabetes": model}, saved, one_person(genhlth=1, _ageg5yr=2))["diabetes"]
    sick = assess({"diabetes": model}, saved, one_person(genhlth=5, _ageg5yr=12, bphigh6=2))["diabetes"]

    assert sick["percentile"] > healthy["percentile"]
    assert sick["flagged"] and not healthy["flagged"]
    assert sick["level"] == "Higher" and healthy["level"] in ("Lower", "Moderate")
    assert 0 <= sick["flag_line"] <= 99


def test_drivers_name_the_factors_that_raise_the_score():
    X, y = make_data()
    model = make_model(X, y)
    up, down = score_drivers(model, one_person(genhlth=5, _ageg5yr=12, bphigh6=2))
    assert "blood pressure" in up and "general health" in up
    # drinks, smoking and the days of poor health are never listed
    assert not any(w in name for name in up + down for w in ("drink", "smok", "days"))


def test_flag_cutoff_matches_predict():
    X, y = make_data()
    model = make_model(X, y)
    person = one_person(genhlth=5, _ageg5yr=12, bphigh6=2)
    assert (model.predict_proba(person)[0, 1] > FLAG_CUTOFF) == bool(model.predict(person)[0])


def test_risk_level_bands():
    assert risk_level(True, 90, 65) == "Higher"
    assert risk_level(False, 50, 65) == "Moderate"     # past half way to the flag line
    assert risk_level(False, 20, 65) == "Lower"
