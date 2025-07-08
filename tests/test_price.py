import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def patch_get_price(monkeypatch):
    async def fake_get_price(market_id: int):
        return {"symbol": "FAKE", "price": 123.456}
    monkeypatch.setattr("app.api.price.get_price", fake_get_price)


def test_read_price():
    response = client.get("/price/1")
    assert response.status_code == 200
    data = response.json()
    assert data["market_id"] == 1
    assert data["price"] == 123.456
    assert "symbol" in data


def test_negative_market_id():
    response = client.get("/price/-1")
    assert response.status_code == 400
    assert response.json()["detail"] == "market_id must be non-negative"


def test_read_price_real_api():
    # 실제 API를 테스트하므로 patch fixture를 사용하지 않음
    response = client.get("/price/1")
    assert response.status_code == 200
    data = response.json()
    assert data["market_id"] == 1
    assert isinstance(data["price"], float)
    assert isinstance(data["symbol"], str)
    assert data["price"] > 0  # 실제 가격이 0보다 큰지 확인