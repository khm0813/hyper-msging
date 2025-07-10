import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


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

@pytest.fixture(autouse=True)
def patch_get_orderbook(monkeypatch):
    async def fake_get_orderbook(symbol: str):
        if symbol == "BTC":
            return {"symbol": "BTC", "bids": [[100, 1], [99, 2]], "asks": [[101, 1], [102, 2]]}
        elif symbol == "EMPTY":
            return {"symbol": "EMPTY", "bids": [], "asks": []}
        raise Exception("Unknown symbol")
    monkeypatch.setattr("app.core.hyperevm_client.get_orderbook", fake_get_orderbook)


def test_read_orderbook():
    response = client.get("/price/orderbook/BTC")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "BTC"
    assert isinstance(data["bids"], list)
    assert isinstance(data["asks"], list)

def test_orderbook_invalid_symbol():
    response = client.get("/orderbook/!@#")
    assert response.status_code == 400 or response.status_code == 404

def test_orderbook_not_found():
    response = client.get("/price/orderbook/EMPTY")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "Orderbook not found" in detail or detail == "Symbol not found: EMPTY"

def test_orderbook_unknown_symbol():
    response = client.get("/price/orderbook/UNKNOWN")
    assert response.status_code == 400 or response.status_code == 404

def test_read_symbols():
    response = client.get("/price/symbols")
    assert response.status_code == 200
    data = response.json()
    assert "BTC" in data["symbols"]
    assert "ETH" in data["symbols"]

def test_orderbook_symbol_not_found():
    response = client.get("/price/orderbook/NOTREAL")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "Symbol not found" in detail or detail == "Not Found"

def test_price_symbol_not_found(monkeypatch):
    async def fake_get_price(market_id: int):
        return {"symbol": "NOTREAL", "price": 1.0}
    monkeypatch.setattr("app.core.hyperevm_client.get_price", fake_get_price)
    response = client.get("/1")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "Symbol not found" in detail or detail == "Not Found"
