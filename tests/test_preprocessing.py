import numpy as np
import pandas as pd
import pytest

from purvarogya import config
from purvarogya.preprocessing import (
    build_clean_dataset,
    build_imputer,
    clean_special_codes,
    create_targets,
    recode_bphigh6,
)


def make_raw_row(**overrides):
    """One valid raw BRFSS-style row, with any column overridden by the test."""
    row = {
        "diabete4": 3, "_michd": 2, "cvdstrk3": 2,
        "genhlth": 2, "_bmi5": 2500, "_smoker3": 4, "_drnkwk2": 0, "_totinda": 1,
        "menthlth": 88, "physhlth": 88, "bphigh6": 3, "_rfchol3": 1,
        "_ageg5yr": 5, "_sex": 1, "income3": 6, "_educag": 3,
    }
    row.update(overrides)
    return row


def test_targets_prediabetes_counts_as_positive():
    df = pd.DataFrame([make_raw_row(diabete4=4), make_raw_row(diabete4=3)])
    out = create_targets(df)
    assert out["diabetes_target"].tolist() == [1, 0]


def test_targets_unknown_codes_are_dropped():
    df = pd.DataFrame([make_raw_row(cvdstrk3=7), make_raw_row(diabete4=9), make_raw_row()])
    out = create_targets(df)
    assert len(out) == 1


def test_88_means_zero_days_not_missing():
    df = pd.DataFrame([make_raw_row(menthlth=88, physhlth=77)])
    out = clean_special_codes(df)
    assert out.loc[0, "menthlth"] == 0
    assert np.isnan(out.loc[0, "physhlth"])


def test_bmi_is_divided_by_100():
    df = pd.DataFrame([make_raw_row(_bmi5=2450)])
    assert clean_special_codes(df).loc[0, "_bmi5"] == 24.5


def test_build_clean_dataset_columns_and_dropping():
    df = pd.DataFrame([make_raw_row(), make_raw_row(genhlth=7)])  # 2nd row has refused genhlth
    out = build_clean_dataset(df)
    assert len(out) == 1
    assert list(out.columns) == config.FEATURES + config.TARGET_COLUMNS


def test_imputer_learns_only_from_training_data():
    train = pd.DataFrame([make_raw_row(_bmi5=2000), make_raw_row(_bmi5=3000)])
    test = pd.DataFrame([make_raw_row(_bmi5=9000), make_raw_row(_bmi5=9000, income3=77)])
    train = clean_special_codes(train)[config.FEATURES]
    test = clean_special_codes(test)[config.FEATURES]
    test.loc[0, "_bmi5"] = np.nan   # a missing BMI in the test set

    imputer = build_imputer().fit(train)
    filled = imputer.transform(test)

    # train median is 25.0; the test rows (BMI 90) must not influence it
    assert filled.loc[0, "_bmi5"] == 25.0
    # the refused income (77 -> NaN) is filled with the most frequent TRAIN value
    assert filled.isna().sum().sum() == 0


def test_age_group_14_becomes_missing_and_row_is_dropped():
    df = pd.DataFrame([make_raw_row(_ageg5yr=14), make_raw_row(_ageg5yr=5)])
    assert np.isnan(clean_special_codes(df).loc[0, "_ageg5yr"])
    assert len(build_clean_dataset(df)) == 1


def test_bphigh6_is_reordered_by_risk():
    df = pd.DataFrame([make_raw_row(bphigh6=3), make_raw_row(bphigh6=4), make_raw_row(bphigh6=1)])
    assert recode_bphigh6(df)["bphigh6"].tolist() == [0, 1, 2]


def test_bphigh6_recode_refuses_to_run_twice():
    df = pd.DataFrame([make_raw_row(bphigh6=3), make_raw_row(bphigh6=1)])
    once = recode_bphigh6(df)          # 3 -> 0 and 1 -> 2, so a 0 now exists
    with pytest.raises(AssertionError):
        recode_bphigh6(once)


def test_drinks_are_divided_by_100_and_refused_stays_missing():
    df = pd.DataFrame([make_raw_row(_drnkwk2=70), make_raw_row(_drnkwk2=99900)])
    out = clean_special_codes(df)
    assert out.loc[0, "_drnkwk2"] == 0.7
    assert np.isnan(out.loc[1, "_drnkwk2"])
