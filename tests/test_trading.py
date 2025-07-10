import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def patch_httpx_get(monkeypatch):
    """HTTP 요청을 모킹하는 fixture"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "address": "0x3F3441234567890abcdef1234567890abcdef1234",
        "signatures": {
            "field-node": "A/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
            "hl-node": "roOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
            "unit-node": "JO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
        },
        "status": "OK"
    }
    mock_response.raise_for_status.return_value = None
    
    def mock_get(url):
        return mock_response
    
    monkeypatch.setattr("httpx.get", mock_get)

@pytest.fixture(autouse=True)
def patch_verify_signatures(monkeypatch):
    """서명 검증 함수를 모킹하는 fixture"""
    def mock_verify_signatures(*args, **kwargs):
        return True
    
    monkeypatch.setattr("app.core.hyperunit_client.verify_signatures", mock_verify_signatures)

def test_gen_wallet_success():
    """지갑 생성 API 성공 테스트"""
    response = client.get("/trading/gen_wallet")
    
    assert response.status_code == 200
    data = response.json()
    
    # 지갑 정보 검증
    assert "wallet" in data
    assert "address" in data["wallet"]
    assert "private_key" in data["wallet"]
    assert data["wallet"]["address"].startswith("0x")
    assert len(data["wallet"]["address"]) == 42  # 이더리움 주소 길이
    assert data["wallet"]["private_key"].startswith("0x")
    assert len(data["wallet"]["private_key"]) == 66  # 32바이트 + 0x
    
    # 입금주소 정보 검증
    assert "deposit_address" in data
    assert "ETH" in data["deposit_address"]
    assert "SOL" in data["deposit_address"]
    
    # ETH 입금주소 검증
    eth_data = data["deposit_address"]["ETH"]
    assert "address" in eth_data
    assert "signatures" in eth_data
    assert "status" in eth_data
    assert eth_data["status"] == "OK"
    assert "field-node" in eth_data["signatures"]
    assert "hl-node" in eth_data["signatures"]
    assert "unit-node" in eth_data["signatures"]
    
    # SOL 입금주소 검증
    sol_data = data["deposit_address"]["SOL"]
    assert "address" in sol_data
    assert "signatures" in sol_data
    assert "status" in sol_data
    assert sol_data["status"] == "OK"
    assert "field-node" in sol_data["signatures"]
    assert "hl-node" in sol_data["signatures"]
    assert "unit-node" in sol_data["signatures"]

def test_gen_wallet_eth_verification_failure(monkeypatch):
    """ETH 서명 검증 실패 테스트"""
    def mock_verify_signatures(*args, **kwargs):
        # ETH 검증만 실패하도록 asset 파라미터 확인
        if kwargs.get("asset") == "eth":
            return False
        return True
    
    monkeypatch.setattr("app.core.hyperunit_client.verify_signatures", mock_verify_signatures)
    
    response = client.get("/trading/gen_wallet")
    
    assert response.status_code == 400
    assert response.json()["detail"] == "ETH 입금 주소 생성 실패"

def test_gen_wallet_sol_verification_failure(monkeypatch):
    """SOL 서명 검증 실패 테스트"""
    def mock_verify_signatures(*args, **kwargs):
        # SOL 검증만 실패하도록 asset 파라미터 확인
        if kwargs.get("asset") == "sol":
            return False
        return True
    
    monkeypatch.setattr("app.core.hyperunit_client.verify_signatures", mock_verify_signatures)
    
    response = client.get("/trading/gen_wallet")
    
    assert response.status_code == 400
    assert response.json()["detail"] == "SOL 입금 주소 생성 실패"

def test_gen_wallet_http_error(monkeypatch):
    """HTTP 요청 실패 테스트"""
    def mock_get(url):
        raise Exception("HTTP Error")
    
    monkeypatch.setattr("httpx.get", mock_get)
    
    response = client.get("/trading/gen_wallet")
    
    assert response.status_code == 500  # FastAPI의 기본 에러 응답

def test_gen_wallet_eth_api_failure(monkeypatch):
    """ETH API 호출 실패 테스트"""
    def mock_get(url):
        if "ethereum" in url:
            raise Exception("ETH API Error")
        # SOL API는 정상 응답
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "address": "0x5A2b31234567890abcdef1234567890abcdef1234",
            "signatures": {
                "field-node": "B/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
                "hl-node": "soOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
                "unit-node": "KO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
            },
            "status": "OK"
        }
        mock_response.raise_for_status.return_value = None
        return mock_response
    
    monkeypatch.setattr("httpx.get", mock_get)
    
    response = client.get("/trading/gen_wallet")
    
    assert response.status_code == 500  # FastAPI의 기본 에러 응답

def test_gen_wallet_response_structure():
    """응답 구조 검증 테스트"""
    response = client.get("/trading/gen_wallet")
    
    assert response.status_code == 200
    data = response.json()
    
    # 필수 필드 존재 확인
    required_fields = ["wallet", "deposit_address"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # wallet 필드 구조 확인
    wallet_fields = ["address", "private_key"]
    for field in wallet_fields:
        assert field in data["wallet"], f"Missing wallet field: {field}"
    
    # deposit_address 필드 구조 확인
    deposit_assets = ["ETH", "SOL"]
    for asset in deposit_assets:
        assert asset in data["deposit_address"], f"Missing deposit asset: {asset}"
        
        asset_data = data["deposit_address"][asset]
        asset_fields = ["address", "signatures", "status"]
        for field in asset_fields:
            assert field in asset_data, f"Missing {asset} field: {field}"
        
        # signatures 구조 확인
        signature_nodes = ["field-node", "hl-node", "unit-node"]
        for node in signature_nodes:
            assert node in asset_data["signatures"], f"Missing signature node: {node}"
            assert isinstance(asset_data["signatures"][node], str), f"Signature {node} should be string"

def test_gen_wallet_address_format():
    """지갑 주소 형식 검증 테스트"""
    response = client.get("/trading/gen_wallet")
    
    assert response.status_code == 200
    data = response.json()
    
    # 메인 지갑 주소 형식 검증
    wallet_address = data["wallet"]["address"]
    assert wallet_address.startswith("0x"), "Wallet address should start with 0x"
    assert len(wallet_address) == 42, "Wallet address should be 42 characters long"
    assert all(c in "0123456789abcdef" for c in wallet_address[2:]), "Wallet address should contain only hex characters"
    
    # 입금주소 형식 검증
    for asset, asset_data in data["deposit_address"].items():
        deposit_address = asset_data["address"]
        assert deposit_address.startswith("0x"), f"{asset} deposit address should start with 0x"
        assert len(deposit_address) >= 42, f"{asset} deposit address should be at least 42 characters long"
        assert all(c in "0123456789abcdef" for c in deposit_address[2:]), f"{asset} deposit address should contain only hex characters" 