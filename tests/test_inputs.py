import pytest
from purvarogya.inputs import age_group, build_person

FEATURE_NAMES = ["_bmi5", "_drnkwk2", "_smoker3", "_rfchol3", "income3",
                 "genhlth", "_totinda", "menthlth", "physhlth", "bphigh6",
                 "_ageg5yr", "_sex", "_educag"]


def test_age_group_edges():
    assert age_group(18) == 1
    assert age_group(24) == 1
    assert age_group(25) == 2
    assert age_group(79) == 12
    assert age_group(80) == 13
    assert age_group(99) == 13


def test_build_person_with_skipped_optionals():
    row = build_person(age=40, sex="Female", height_cm=165, weight_kg=70,
                       general_health="Good", blood_pressure="No",
                       cholesterol="Not sure", feature_names=FEATURE_NAMES)
    assert list(row.columns) == FEATURE_NAMES
    assert row.shape == (1, 13)
    assert row.loc[0, "_bmi5"] == pytest.approx(70 / 1.65 ** 2)
    assert row.loc[0, "_ageg5yr"] == 5
    assert row.loc[0, "_sex"] == 2
    assert row.loc[0, "genhlth"] == 3
    assert row.loc[0, "bphigh6"] == 0
    assert row.loc[0, "_rfchol3"] == 1
    # skipped optionals -> typical answers
    assert row.loc[0, "_smoker3"] == 4
    assert row.loc[0, "_totinda"] == 1
    assert row.loc[0, "_drnkwk2"] == 0.0
    assert row.loc[0, "income3"] == 7
    assert row.loc[0, "_educag"] == 4


def test_build_person_with_optionals_given():
    row = build_person(age=60, sex="Male", height_cm=175, weight_kg=90,
                       general_health="Poor", blood_pressure="Yes",
                       cholesterol="Yes", feature_names=FEATURE_NAMES,
                       smoking="Every day", activity="No", drinks=3.5,
                       physical_days=10, mental_days=5)
    assert row.loc[0, "_smoker3"] == 1
    assert row.loc[0, "_totinda"] == 2
    assert row.loc[0, "_drnkwk2"] == 3.5
    assert row.loc[0, "physhlth"] == 10
    assert row.loc[0, "menthlth"] == 5