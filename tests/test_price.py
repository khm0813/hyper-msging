import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def patch_get_price(monkeypatch):
    async def fake_get_price(market_id: int):
        return 123.456
    monkeypatch.setattr("app.api.price.get_price", fake_get_price)


def test_read_price():
    response = client.get("/price/1")
    assert response.status_code == 200
    data = response.json()
    assert data["market_id"] == 1
    assert data["price"] == 123.456


def test_negative_market_id():
    response = client.get("/price/-1")
    assert response.status_code == 400
    assert response.json()["detail"] == "market_id must be non-negative"