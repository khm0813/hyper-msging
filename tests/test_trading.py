import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import base64
import time
from app.main import app

client = TestClient(app)

class TestTradingAPI:
    """Trading API 테스트 클래스"""
    
    @patch('app.api.trading.httpx.get')
    @patch('app.api.trading.Account.create')
    def test_gen_wallet_success(self, mock_account_create, mock_httpx_get):
        """지갑 생성 API 성공 테스트"""
        # Mock 지갑 생성
        mock_account = MagicMock()
        mock_account.address = "0x1234567890abcdef1234567890abcdef1234567890"
        mock_account.key.hex.return_value = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        mock_account_create.return_value = mock_account
        
        # Mock HyperUnit API 응답
        mock_eth_response = MagicMock()
        mock_eth_response.json.return_value = {
            "address": "0x3F344...",
            "signatures": {
                "field-node": "A/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
                "hl-node": "roOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
                "unit-node": "JO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
            },
            "status": "OK"
        }
        mock_eth_response.raise_for_status.return_value = None
        
        mock_sol_response = MagicMock()
        mock_sol_response.json.return_value = {
            "address": "0x5A2b3...",
            "signatures": {
                "field-node": "B/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
                "hl-node": "soOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
                "unit-node": "KO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
            },
            "status": "OK"
        }
        mock_sol_response.raise_for_status.return_value = None
        
        # 두 번의 API 호출에 대해 다른 응답 반환
        mock_httpx_get.side_effect = [mock_eth_response, mock_sol_response]
        
        response = client.get("/trading/gen_wallet")
        
        assert response.status_code == 200
        data = response.json()
        assert "wallet" in data
        assert "deposit_address" in data
        assert data["wallet"]["address"] == "0x1234567890abcdef1234567890abcdef1234567890"
        assert "ETH" in data["deposit_address"]
        assert "SOL" in data["deposit_address"]

    def test_place_order_success(self):
        """주문 실행 API 성공 테스트"""
        order_data = {
            "symbol": "BTC",
            "side": "buy",
            "size": 1000.0,
            "order_type": "market"
        }
        
        response = client.post("/trading/place_order", json=order_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["symbol"] == "BTC"
        assert data["side"] == "buy"
        assert data["size"] == 1000.0
        assert "order_id" in data

    def test_place_order_invalid_side(self):
        """잘못된 side 파라미터 테스트"""
        order_data = {
            "symbol": "BTC",
            "side": "invalid",
            "size": 1000.0
        }
        
        response = client.post("/trading/place_order", json=order_data)
        
        assert response.status_code == 400
        assert "side must be 'buy' or 'sell'" in response.json()["detail"]

    def test_place_order_invalid_order_type(self):
        """잘못된 order_type 파라미터 테스트"""
        order_data = {
            "symbol": "BTC",
            "side": "buy",
            "size": 1000.0,
            "order_type": "invalid"
        }
        
        response = client.post("/trading/place_order", json=order_data)
        
        assert response.status_code == 400
        assert "order_type must be 'market' or 'limit'" in response.json()["detail"]

    def test_place_order_limit_without_price(self):
        """지정가 주문시 가격 누락 테스트"""
        order_data = {
            "symbol": "BTC",
            "side": "buy",
            "size": 1000.0,
            "order_type": "limit"
        }
        
        response = client.post("/trading/place_order", json=order_data)
        
        assert response.status_code == 400
        assert "price is required for limit orders" in response.json()["detail"]

    @patch('app.api.trading.get_positions_real')
    def test_get_positions(self, mock_get_positions):
        """포지션 조회 API 테스트"""
        address = "0x1234567890abcdef1234567890abcdef1234567890"
        
        # Mock 응답 설정
        mock_positions_data = {
            "address": address,
            "positions": [
                {
                    "symbol": "BTC",
                    "side": "long",
                    "size": 1000.0,
                    "entry_price": 108000.0,
                    "mark_price": 108889.0,
                    "unrealized_pnl": 8.23,
                    "realized_pnl": 0.0,
                    "liquidation_price": 95000.0
                }
            ],
            "total_unrealized_pnl": 8.23,
            "total_realized_pnl": 0.0
        }
        mock_get_positions.return_value = mock_positions_data
        
        response = client.get(f"/trading/positions/{address}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == address
        assert "positions" in data
        assert "total_unrealized_pnl" in data
        assert "total_realized_pnl" in data

    @patch('app.api.trading.get_account_info_real')
    def test_get_account_info(self, mock_get_account_info):
        """계정 정보 조회 API 테스트"""
        address = "0x1234567890abcdef1234567890abcdef1234567890"
        
        # Mock 응답 설정
        mock_account_info = {
            "address": address,
            "total_balance": 1000.0,
            "available_balance": 500.0,
            "margin_used": 500.0,
            "margin_ratio": 0.5,
            "positions": []
        }
        mock_get_account_info.return_value = mock_account_info
        
        response = client.get(f"/trading/account/{address}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == address
        assert "total_balance" in data
        assert "available_balance" in data
        assert "margin_used" in data
        assert "margin_ratio" in data
        assert "positions" in data

    @patch('app.api.trading.close_position_real')
    def test_close_position(self, mock_close_position):
        """포지션 종료 API 테스트"""
        # Mock 응답 설정
        mock_result = {
            "success": True,
            "symbol": "BTC",
            "side": "short",
            "ratio": 0.5,
            "orders": [
                {
                    "order_id": "close_123",
                    "symbol": "BTC",
                    "side": "buy",
                    "size": 0.000325,
                    "price": None,
                    "order_type": "market",
                    "status": "submitted",
                    "reduce_only": True
                }
            ],
            "total_closed_size": 0.000325,
            "status": "submitted",
            "message": "Position close orders submitted for BTC"
        }
        mock_close_position.return_value = mock_result
        
        request_data = {
            "symbol": "BTC",
            "address": "0x1234567890abcdef1234567890abcdef1234567890",
            "side": "short",
            "ratio": 0.5,
            "order_type": "market"
        }
        
        response = client.post("/trading/close_position", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["symbol"] == "BTC"
        assert data["side"] == "short"
        assert data["ratio"] == 0.5
        assert "orders" in data
        assert data["status"] == "submitted"

    def test_close_position_invalid_ratio(self):
        """잘못된 비율로 포지션 종료 테스트"""
        request_data = {
            "symbol": "BTC",
            "address": "0x1234567890abcdef1234567890abcdef1234567890",
            "ratio": 1.5  # 1.0을 초과하는 비율
        }
        
        response = client.post("/trading/close_position", json=request_data)
        
        assert response.status_code == 400
        assert "ratio must be between 0.0 and 1.0" in response.json()["detail"]

    def test_close_position_invalid_order_type(self):
        """잘못된 주문 타입으로 포지션 종료 테스트"""
        request_data = {
            "symbol": "BTC",
            "address": "0x1234567890abcdef1234567890abcdef1234567890",
            "order_type": "invalid"
        }
        
        response = client.post("/trading/close_position", json=request_data)
        
        assert response.status_code == 400
        assert "order_type must be 'market' or 'limit'" in response.json()["detail"]

    def test_close_position_limit_without_price(self):
        """지정가 주문시 가격 누락 테스트"""
        request_data = {
            "symbol": "BTC",
            "address": "0x1234567890abcdef1234567890abcdef1234567890",
            "order_type": "limit"
            # price 누락
        }
        
        response = client.post("/trading/close_position", json=request_data)
        
        assert response.status_code == 400
        assert "price is required for limit orders" in response.json()["detail"]

    def test_get_order_history(self):
        """주문 내역 조회 API 테스트"""
        address = "0x1234567890abcdef1234567890abcdef1234567890"
        
        response = client.get(f"/trading/order_history/{address}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == address
        assert "orders" in data
        assert "total_count" in data

    def test_get_order_history_with_limit(self):
        """주문 내역 조회 API (limit 파라미터 포함) 테스트"""
        address = "0x1234567890abcdef1234567890abcdef1234567890"
        
        response = client.get(f"/trading/order_history/{address}?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == address
        assert "orders" in data
        assert "total_count" in data
    