"""Tests for the FastAPI app. TestClient calls the API without a real server."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

VALID_PERSON = {
    "age": 60,
    "sex": "Male",
    "height_cm": 170,
    "weight_kg": 95,
    "general_health": "Fair",
    "blood_pressure": "Yes",
    "cholesterol": "Yes",
}


@pytest.fixture(scope="module")
def client():
    # the with-block runs the startup code, so the models get loaded
    with TestClient(app) as c:
        yield c


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["models_loaded"] == ["diabetes", "cvd", "stroke"]


def test_predict_returns_all_three_diseases(client):
    response = client.post("/predict", json=VALID_PERSON)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {"diabetes", "cvd", "stroke"}
    for result in data.values():
        assert set(result) == {"flagged", "level", "percentile",
                               "flag_line", "pushing_up", "pulling_down"}
        assert result["level"] in ("Lower", "Moderate", "Higher")
        assert 0 <= result["percentile"] <= 100


def test_optional_answers_are_accepted(client):
    person = {**VALID_PERSON, "smoking": "Never", "activity": "Yes",
              "drinks": 2, "physical_days": 3, "mental_days": 1}
    assert client.post("/predict", json=person).status_code == 200


def test_questions_we_never_asked_are_not_shown_as_reasons(client):
    data = client.post("/predict", json=VALID_PERSON).json()
    for result in data.values():
        shown = result["pushing_up"] + result["pulling_down"]
        assert "education" not in shown
        assert "income" not in shown


def test_age_below_18_is_rejected(client):
    response = client.post("/predict", json={**VALID_PERSON, "age": 5})
    assert response.status_code == 422


def test_impossible_bmi_is_rejected(client):
    # 220 cm and 30 kg gives a BMI of about 6
    person = {**VALID_PERSON, "height_cm": 220, "weight_kg": 30}
    assert client.post("/predict", json=person).status_code == 422


def test_unknown_choice_is_rejected(client):
    response = client.post("/predict", json={**VALID_PERSON, "general_health": "Great"})
    assert response.status_code == 422


def test_missing_required_answer_is_rejected(client):
    person = {k: v for k, v in VALID_PERSON.items() if k != "blood_pressure"}
    assert client.post("/predict", json=person).status_code == 422


def test_home_page_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "PurvAarogya" in response.text


def test_static_assets_return_ok(client):
    for path in ("/static/app.js", "/static/style.css"):
        response = client.get(path)
        assert response.status_code == 200
