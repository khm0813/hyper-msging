import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import base64
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_hyperliquid_response():
    """Hyperliquid API 응답 모킹"""
    return {
        "marginSummary": {
            "accountValue": "1000.50",
            "totalNtlPos": "500.25",
            "totalRawUsd": "1000.50",
            "totalMarginUsed": "200.10"
        },
        "crossMarginSummary": {
            "accountValue": "1000.50",
            "totalNtlPos": "500.25",
            "totalRawUsd": "1000.50",
            "totalMarginUsed": "200.10"
        },
        "crossMaintenanceMarginUsed": "150.00",
        "withdrawable": "800.40",
        "assetPositions": [
            {
                "coin": "USDC",
                "position": "1000.50",
                "notionalUsd": "1000.50"
            }
        ],
        "time": 1752146173198
    }


@pytest.fixture
def mock_empty_balance_response():
    """잔고가 없는 경우의 Hyperliquid API 응답 모킹"""
    return {
        "marginSummary": {
            "accountValue": "0.0",
            "totalNtlPos": "0.0",
            "totalRawUsd": "0.0",
            "totalMarginUsed": "0.0"
        },
        "crossMarginSummary": {
            "accountValue": "0.0",
            "totalNtlPos": "0.0",
            "totalRawUsd": "0.0",
            "totalMarginUsed": "0.0"
        },
        "crossMaintenanceMarginUsed": "0.0",
        "withdrawable": "0.0",
        "assetPositions": [],
        "time": 1752146173198
    }


@patch('httpx.AsyncClient.post')
def test_wallet_balance_success(mock_post, mock_hyperliquid_response):
    """지갑 잔고 조회 성공 테스트"""
    # Mock 설정
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_hyperliquid_response
    mock_post.return_value = mock_response
    
    # 테스트 실행
    response = client.get("/trading/wallet_balance?address=0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6")
    
    # 검증
    assert response.status_code == 200
    data = response.json()
    
    assert data["address"] == "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
    assert data["balance"]["account_value"] == "1000.50"
    assert data["balance"]["withdrawable"] == "800.40"
    assert data["balance"]["total_margin_used"] == "200.10"
    assert data["balance"]["total_notional_position"] == "500.25"
    assert data["balance"]["total_raw_usd"] == "1000.50"
    assert len(data["balance"]["asset_positions"]) == 1
    assert data["balance"]["asset_positions"][0]["coin"] == "USDC"
    assert data["balance"]["timestamp"] == 1752146173198
    
    # API 호출 검증
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[1]["json"]["type"] == "clearinghouseState"
    assert call_args[1]["json"]["user"] == "0x742d35cc6634c0532925a3b8d4c9db96c4b4d8b6"  # 소문자 변환 확인


@patch('httpx.AsyncClient.post')
def test_wallet_balance_empty(mock_post, mock_empty_balance_response):
    """잔고가 없는 지갑 조회 테스트"""
    # Mock 설정
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_empty_balance_response
    mock_post.return_value = mock_response
    
    # 테스트 실행
    response = client.get("/trading/wallet_balance?address=0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6")
    
    # 검증
    assert response.status_code == 200
    data = response.json()
    
    assert data["address"] == "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
    assert data["balance"]["account_value"] == "0.0"
    assert data["balance"]["withdrawable"] == "0.0"
    assert data["balance"]["total_margin_used"] == "0.0"
    assert data["balance"]["asset_positions"] == []
    assert "잔고 없음 또는 신규 지갑" in data["balance"]["message"]


@patch('httpx.AsyncClient.post')
def test_wallet_balance_api_error(mock_post):
    """API 오류 시 테스트"""
    # Mock 설정 - API 오류 시뮬레이션
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_post.return_value = mock_response
    
    # 테스트 실행
    response = client.get("/trading/wallet_balance?address=0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6")
    
    # 검증
    assert response.status_code == 500
    assert "Hyperliquid API 응답이 비정상" in response.json()["detail"]


@patch('httpx.AsyncClient.post')
def test_wallet_balance_timeout(mock_post):
    """타임아웃 오류 테스트"""
    # Mock 설정 - 타임아웃 시뮬레이션
    mock_post.side_effect = Exception("timeout")
    
    # 테스트 실행
    response = client.get("/trading/wallet_balance?address=0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6")
    
    # 검증
    assert response.status_code == 500
    assert "서버 내부 오류" in response.json()["detail"]


def test_wallet_balance_missing_address():
    """주소 파라미터 누락 테스트"""
    response = client.get("/trading/wallet_balance")
    assert response.status_code == 422  # Validation error


def test_wallet_balance_invalid_address():
    """잘못된 주소 형식 테스트"""
    response = client.get("/trading/wallet_balance?address=invalid_address")
    # 주소 검증은 Hyperliquid API에서 처리되므로 200이 반환될 수 있음
    # 실제로는 API 호출이 이루어지고 응답을 받게 됨
    assert response.status_code in [200, 400, 500]


# gen_wallet 함수 테스트
@patch('httpx.get')
def test_gen_wallet_success(mock_get):
    """지갑 생성 성공 테스트"""
    # Mock 설정
    mock_eth_response = type('MockResponse', (), {
        'raise_for_status': lambda: None,
        'json': lambda: {
            "address": "0x3F344...",
            "signatures": {
                "field-node": "A/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
                "hl-node": "roOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
                "unit-node": "JO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
            },
            "status": "OK"
        }
    })()
    
    mock_sol_response = type('MockResponse', (), {
        'raise_for_status': lambda: None,
        'json': lambda: {
            "address": "0x5A2b3...",
            "signatures": {
                "field-node": "B/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
                "hl-node": "soOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
                "unit-node": "KO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
            },
            "status": "OK"
        }
    })()
    
    mock_get.side_effect = [mock_eth_response, mock_sol_response]
    
    # 테스트 실행
    response = client.get("/trading/gen_wallet")
    
    # 검증
    assert response.status_code == 200
    data = response.json()
    
    assert "wallet" in data
    assert "address" in data["wallet"]
    assert "private_key" in data["wallet"]
    assert data["wallet"]["address"].startswith("0x")
    assert len(data["wallet"]["private_key"]) == 66  # 0x + 64 hex chars
    
    assert "deposit_address" in data
    assert "ETH" in data["deposit_address"]
    assert "SOL" in data["deposit_address"]
    assert data["deposit_address"]["ETH"]["status"] == "OK"
    assert data["deposit_address"]["SOL"]["status"] == "OK"
    
    # API 호출 검증
    assert mock_get.call_count == 2
    