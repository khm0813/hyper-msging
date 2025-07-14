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
        mock_account.address = "0x1234567890123456789012345678901234567890"
        mock_account.key.hex.return_value = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        mock_account_create.return_value = mock_account
        
        # Mock ETH 입금 주소 생성 응답 (실제 서명과 유사한 형태)
        mock_eth_response = MagicMock()
        mock_eth_response.json.return_value = {
            "address": "0xETH_DEPOSIT_ADDRESS",
            "signatures": {
                "field-node": "A/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
                "hl-node": "roOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
                "unit-node": "JO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
            },
            "status": "OK"
        }
        mock_eth_response.raise_for_status.return_value = None
        
        # Mock SOL 입금 주소 생성 응답
        mock_sol_response = MagicMock()
        mock_sol_response.json.return_value = {
            "address": "0xSOL_DEPOSIT_ADDRESS",
            "signatures": {
                "field-node": "B/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
                "hl-node": "soOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
                "unit-node": "KO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
            },
            "status": "OK"
        }
        mock_sol_response.raise_for_status.return_value = None
        
        # Mock httpx.get 호출 순서 설정
        mock_httpx_get.side_effect = [mock_eth_response, mock_sol_response]
        
        # API 호출
        response = client.get("/trading/gen_wallet")
        
        # 응답 검증
        assert response.status_code == 200
        data = response.json()
        
        assert "wallet" in data
        assert data["wallet"]["address"] == "0x1234567890123456789012345678901234567890"
        assert data["wallet"]["private_key"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        
        assert "deposit_address" in data
        assert "ETH" in data["deposit_address"]
        assert "SOL" in data["deposit_address"]
        assert data["deposit_address"]["ETH"]["address"] == "0xETH_DEPOSIT_ADDRESS"
        assert data["deposit_address"]["SOL"]["address"] == "0xSOL_DEPOSIT_ADDRESS"
    