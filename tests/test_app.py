import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


FROSTY = {
    "air_temp_c": 1.5,
    "dew_point_c": -1.0,
    "wind_speed_ms": 0.8,
    "cloud_cover_pct": 10,
}

MILD = {
    "air_temp_c": 9.0,
    "dew_point_c": 4.0,
    "wind_speed_ms": 3.5,
    "cloud_cover_pct": 80,
}


def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_returns_valid_probability_and_threshold(client):
    response = client.post("/predict", json=FROSTY)

    assert response.status_code == 200
    result = response.json()
    assert 0 <= result["frost_probability"] <= 1
    assert result["threshold"] == 0.35


def test_frosty_reading_scores_higher_than_mild(client):
    frosty = client.post("/predict", json=FROSTY)
    mild = client.post("/predict", json=MILD)

    assert frosty.status_code == 200
    assert mild.status_code == 200
    assert (
        frosty.json()["frost_probability"]
        > mild.json()["frost_probability"]
    )
    assert frosty.json()["alert"] is True
    assert mild.json()["alert"] is False


@pytest.mark.parametrize(
    "reading",
    [
        {**FROSTY, "wind_speed_ms": -1},
        {**FROSTY, "cloud_cover_pct": 101},
    ],
)
def test_impossible_reading_is_rejected(client, reading):
    response = client.post("/predict", json=reading)
    assert response.status_code == 422
