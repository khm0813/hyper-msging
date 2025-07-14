import base64
import hashlib
from typing import Dict, Optional, List
from dataclasses import dataclass
from eth_keys.datatypes import PublicKey, Signature
import httpx
import json
import time
from web3 import Web3, Account
from app.config import settings
import hmac
import struct
from eth_account import Account
from eth_account.messages import encode_defunct
# from app.core.hyperliquid_sdk_client import close_position_real  # Remove this import to avoid circular import
import asyncio

# Hyperliquid 서명 관련 함수들
def generate_hyperliquid_signature(data: dict, private_key: str) -> str:
    """
    Hyperliquid API용 EIP-191 이더리움 서명 생성
    Args:
        data: 서명할 args dict
        private_key: 이더리움 개인키(hex)
    Returns:
        0x로 시작하는 hex string 서명
    """
    msg = json.dumps(data, separators=(',', ':'))
    message = encode_defunct(text=msg)
    signed_message = Account.sign_message(message, private_key)
    return signed_message.signature.hex()

def create_signed_order_request(order_data: Dict, private_key: str) -> Dict:
    """
    서명된 주문 요청 생성
    
    Args:
        order_data: 주문 데이터
        private_key: 개인키
    
    Returns:
        서명된 요청 데이터
    """
    try:
        # 1. 타임스탬프 추가
        timestamp = int(time.time() * 1000)  # 밀리초 단위
        order_data_with_timestamp = {
            **order_data,
            "timestamp": timestamp
        }
        
        # 2. 서명 생성
        signature = generate_hyperliquid_signature(order_data_with_timestamp, private_key)
        
        # 3. 서명된 요청 구성
        signed_request = {
            "action": "order",
            "args": order_data_with_timestamp,
            "signature": signature
        }
        
        return signed_request
        
    except Exception as e:
        raise Exception(f"Signed request creation failed: {str(e)}")

# Hyperliquid 거래 관련 함수들
def normalize_hyperliquid_address(address: str) -> str:
    """
    Hyperliquid API용 주소 정규화
    - 0x 제거하고 소문자로 변환
    """
    return address.lower().replace("0x", "")

async def get_user_state(address: str) -> Dict:
    """
    Hyperliquid에서 사용자 상태 정보 조회
    - 포지션, 잔고, 마진 정보 등
    """
    url = f"{settings.HYPERLIQUID_API_URL}/info"
    payload = {
        "type": "clearinghouseState",
        "user": normalize_hyperliquid_address(address)
    }
    print(f"[get_user_state] 요청 payload: {payload}")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        print(f"[get_user_state] 응답 status: {response.status_code}")
        print(f"[get_user_state] 응답 본문: {response.text}")
        response.raise_for_status()
        return response.json()

async def get_account_info_real(address: str) -> Dict:
    """
    Hyperliquid에서 실제 계정 정보 조회
    - 잔고, 포지션, 마진 정보 등을 종합적으로 반환
    """
    address = normalize_hyperliquid_address(address)
    print(address)
    try:
        # 1. 사용자 상태 정보 조회
        user_state = await get_user_state(address)
        print(user_state)
        
        # 2. 포지션 정보 조회
        positions_data = await get_positions_real(address)
        
        # 3. 계정 정보 구성
        account_info = {
            "address": address,
            "total_balance": 0.0,
            "available_balance": 0.0,
            "margin_used": 0.0,
            "margin_ratio": 0.0,
            "positions": positions_data.get("positions", [])
        }
        
        # 4. 잔고 정보 계산 (user_state에서 추출)
        if "assetPositions" in user_state:
            for asset_pos in user_state["assetPositions"]:
                position_data = asset_pos.get("position", {})
                if isinstance(position_data, dict):
                    position_value = float(position_data.get("szi", "0"))
                else:
                    position_value = float(position_data) if position_data != "0" else 0
                
                if position_value != 0:
                    account_info["total_balance"] += abs(position_value)
                    account_info["margin_used"] += abs(position_value)
        
        # 5. 마진 비율 계산
        if account_info["total_balance"] > 0:
            account_info["margin_ratio"] = account_info["margin_used"] / account_info["total_balance"]
        
        # 6. 사용 가능한 잔고 계산
        account_info["available_balance"] = account_info["total_balance"] - account_info["margin_used"]
        
        return account_info
        
    except Exception as e:
        raise Exception(f"Failed to fetch account info: {str(e)}")

async def get_positions_real(address: str) -> Dict:
    """
    Hyperliquid에서 실제 포지션 정보 조회
    """
    address = normalize_hyperliquid_address(address)
    try:
        # 1. 사용자 상태 정보 조회
        user_state = await get_user_state(address)
        
        # 2. 포지션 정보 추출
        positions = []
        total_unrealized_pnl = 0.0
        total_realized_pnl = 0.0
        
        if "assetPositions" in user_state:
            for asset_pos in user_state["assetPositions"]:
                position_data = asset_pos.get("position", {})
                
                if isinstance(position_data, dict):
                    position_value = float(position_data.get("szi", "0"))
                    symbol = position_data.get("coin", "UNKNOWN")
                    entry_price = float(position_data.get("entryPx", "0"))
                    unrealized_pnl = float(position_data.get("unrealizedPnl", "0"))
                    position_value_usd = float(position_data.get("positionValue", "0"))
                else:
                    position_value = float(position_data) if position_data != "0" else 0
                    symbol = asset_pos.get("coin", "UNKNOWN")
                    entry_price = float(asset_pos.get("entryPx", "0"))
                    unrealized_pnl = 0.0
                    position_value_usd = 0.0
                
                if position_value != 0:  # 포지션이 있는 경우만
                    side = "long" if position_value > 0 else "short"
                    size = abs(position_value)
                    
                    # 마크가격은 현재가로 대체 (실제로는 별도 API 호출 필요)
                    mark_price = entry_price  # 임시로 진입가격 사용
                    
                    total_unrealized_pnl += unrealized_pnl
                    
                    position_info = {
                        "symbol": symbol,
                        "side": side,
                        "size": size,
                        "entry_price": entry_price,
                        "mark_price": mark_price,
                        "unrealized_pnl": unrealized_pnl,
                        "realized_pnl": 0.0,  # TODO: 실제 실현 손익 계산
                        "liquidation_price": None  # TODO: 청산가격 계산
                    }
                    
                    positions.append(position_info)
        
        return {
            "address": address,
            "positions": positions,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl
        }
        
    except Exception as e:
        raise Exception(f"Failed to fetch positions: {str(e)}")

async def get_open_orders(address: str) -> List[Dict]:
    """
    미체결 주문 조회
    """
    url = f"{settings.HYPERLIQUID_API_URL}/info"
    payload = {
        "type": "openOrders",
        "user": normalize_hyperliquid_address(address)
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

async def place_order(
    private_key: str,
    symbol: str,
    side: str,  # "buy" or "sell"
    size: float,
    price: Optional[float] = None,
    order_type: str = "market",
    reduce_only: bool = False
) -> Dict:
    """
    Hyperliquid에 실제 주문 실행 - 실제 Hyperliquid API 사용
    
    Args:
        private_key: 지갑 개인키
        symbol: 거래 심볼 (예: "BTC")
        side: "buy" (Long) 또는 "sell" (Short)
        size: 포지션 크기 (USD)
        price: 지정가 주문시 가격
        order_type: "market" 또는 "limit"
        reduce_only: 포지션 감소만 허용
    
    Returns:
        주문 결과
    """
    try:
        # 1. 계정 생성
        account = Account.from_key(private_key)
        
        # 2. Hyperliquid API 형식으로 주문 데이터 구성
        order_data = {
            "user": normalize_hyperliquid_address(account.address),
            "coin": symbol,
            "is_buy": side == "buy",
            "sz": str(size),
            "limit_px": str(price) if price and order_type == "limit" else "0",
            "reduce_only": reduce_only
        }
        
        # 3. 서명 생성
        signature = generate_hyperliquid_signature(order_data, private_key)
        
        # 4. 서명된 요청 구성
        signed_request = {
            "action": "order",
            "args": order_data,
            "signature": signature
        }
        
        # 5. 실제 Hyperliquid API 호출
        url = f"{settings.HYPERLIQUID_API_URL}/exchange"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=signed_request)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "order_id": result.get("response", {}).get("data", {}).get("oid", f"order_{int(time.time())}"),
                    "symbol": symbol,
                    "side": side,
                    "size": size,
                    "price": price,
                    "order_type": order_type,
                    "status": "submitted",
                    "timestamp": int(time.time()),
                    "api_response": result
                }
            else:
                # API 오류 처리
                error_detail = f"API Error: {response.status_code}"
                try:
                    error_response = response.json()
                    error_detail += f" - {error_response}"
                except:
                    error_detail += f" - {response.text}"
                
                raise Exception(f"Order placement failed: {error_detail}")
        
    except Exception as e:
        raise Exception(f"Order placement failed: {str(e)}")

async def cancel_order(private_key: str, order_id: str) -> Dict:
    """
    실제 주문 취소 - 실제 Hyperliquid API 사용
    """
    try:
        account = Account.from_key(private_key)
        
        # Hyperliquid API 형식으로 취소 데이터 구성
        cancel_data = {
            "user": normalize_hyperliquid_address(account.address),
            "oid": order_id
        }
        
        # 서명 생성
        signature = generate_hyperliquid_signature(cancel_data, private_key)
        
        # 서명된 요청 구성
        signed_request = {
            "action": "cancel",
            "args": cancel_data,
            "signature": signature
        }
        
        # 실제 Hyperliquid API 호출
        url = f"{settings.HYPERLIQUID_API_URL}/exchange"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=signed_request)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "order_id": order_id,
                    "status": "cancelled",
                    "api_response": result
                }
            else:
                # API 오류 처리
                error_detail = f"API Error: {response.status_code}"
                try:
                    error_response = response.json()
                    error_detail += f" - {error_response}"
                except:
                    error_detail += f" - {response.text}"
                
                raise Exception(f"Order cancellation failed: {error_detail}")
        
    except Exception as e:
        raise Exception(f"Order cancellation failed: {str(e)}")

# Hyperliquid asset symbol to id 매핑 (공식 문서/SDK 참고, 예시)
ASSET_ID_MAP = {
    "BTC": 1,
    "ETH": 2,
    # 필요시 추가
}

def generate_hyperliquid_signature_v2(action: dict, nonce: int, private_key: str) -> str:
    """
    Hyperliquid v2 주문용 EIP-191 서명 (action+nonce 직렬화)
    """
    msg = json.dumps({"action": action, "nonce": nonce}, separators=(',', ':'))
    message = encode_defunct(text=msg)
    signed_message = Account.sign_message(message, private_key)
    return signed_message.signature.hex()

async def close_position_real(
    address: str,
    symbol: str,
    side: Optional[str] = None,
    ratio: float = 1.0,
    price: Optional[float] = None,
    order_type: str = "market"
) -> Dict:
    """
    Hyperliquid SDK 기반 포지션 청산 (app.core.hyperliquid_sdk_client.close_position_real 위임)
    """
    from app.core import hyperliquid_sdk_client  # Local import to avoid circular import
    # SDK 함수에 인자 전달 (price/order_type은 현재 SDK에서 사용하지 않으나, 인터페이스 유지)
    result = await hyperliquid_sdk_client.close_position_real(
        address=address,
        symbol=symbol,
        side=side if side is not None else "",  # SDK expects str, so pass empty string if None
        ratio=ratio,
        price=price if price is not None else 0.0,
        order_type=order_type
    )
    return result

async def get_trade_history(address: str, limit: int = 50) -> List[Dict]:
    """
    거래 내역 조회
    """
    try:
        url = f"{settings.HYPERLIQUID_API_URL}/info"
        payload = {
            "type": "userFills",
            "user": normalize_hyperliquid_address(address)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            fills = response.json()
            
            # 최근 거래만 반환
            return fills[:limit]
            
    except Exception as e:
        raise Exception(f"Failed to fetch trade history: {str(e)}") 