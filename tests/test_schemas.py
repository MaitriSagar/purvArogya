from typing import get_args

import pytest
from pydantic import ValidationError

from api.schemas import PredictRequest
from purvarogya import inputs

valid = dict(age=40, sex="Female", height_cm=165, weight_kg=70,
             general_health="Good", blood_pressure="No", cholesterol="Not sure")


def test_valid_request_optionals_default_to_none():
    req = PredictRequest(**valid)
    assert req.smoking is None
    assert req.drinks is None


def test_age_limits():
    with pytest.raises(ValidationError):
        PredictRequest(**{**valid, "age": 17})
    with pytest.raises(ValidationError):
        PredictRequest(**{**valid, "age": 100})
    assert PredictRequest(**{**valid, "age": 99}).age == 99


def test_unknown_choice_rejected():
    with pytest.raises(ValidationError):
        PredictRequest(**{**valid, "sex": "Femal"})


def test_unrealistic_bmi_rejected():
    # 200 cm and 30 kg is a BMI of 7.5
    with pytest.raises(ValidationError):
        PredictRequest(**{**valid, "height_cm": 200, "weight_kg": 30})


def test_choices_match_inputs_maps():
    fields = {"sex": inputs.SEX, "general_health": inputs.GENERAL_HEALTH,
              "blood_pressure": inputs.BLOOD_PRESSURE, "cholesterol": inputs.CHOLESTEROL}
    for name, mapping in fields.items():
        allowed = get_args(PredictRequest.model_fields[name].annotation)
        assert set(allowed) == set(mapping)