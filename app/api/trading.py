from fastapi import APIRouter, HTTPException
import httpx
from web3 import Web3, Account
from app.config import settings
from app.core.hyperunit_client import verify_signatures, verify_deposit_address_signatures, Proposal
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import time

router = APIRouter()

# Pydantic 모델 정의
class OrderRequest(BaseModel):
    """주문 요청 모델"""
    symbol: str
    side: str  # "buy" (Long) 또는 "sell" (Short)
    size: float  # 포지션 크기 (USD 기준)
    price: Optional[float] = None  # 지정가 주문시에만 사용
    order_type: str = "market"  # "market" 또는 "limit"
    reduce_only: bool = False  # 포지션 감소만 허용
    time_in_force: str = "Gtc"  # Good till cancelled

class PositionInfo(BaseModel):
    """포지션 정보 모델"""
    symbol: str
    side: str  # "long" 또는 "short"
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    realized_pnl: float
    liquidation_price: Optional[float] = None

class AccountInfo(BaseModel):
    """계정 정보 모델"""
    address: str
    total_balance: float
    available_balance: float
    margin_used: float
    margin_ratio: float
    positions: list[PositionInfo]

class ClosePositionRequest(BaseModel):
    """포지션 종료 요청 모델"""
    symbol: str
    address: str
    side: Optional[str] = None  # "long" 또는 "short" (생략시 모든 포지션)
    ratio: float = 1.0  # 종료할 비율 (0.0 ~ 1.0, 기본값: 1.0 = 전체 종료)
    price: Optional[float] = None  # 지정가 종료시 가격 (시장가 종료시 생략)
    order_type: str = "market"  # "market" 또는 "limit"

@router.get("/gen_wallet")
async def gen_wallet():
    '''
    1. 지갑 생성
    2. 반환 구조 생성
    3. 입금주소 생성
    '''

    # 1. 지갑 생성
    account = Account.create()
    # 2. 반환 구조 생성

    # 3. 입금주소 생성
    '''
	•	src_chain = 자산이 존재하는 체인 ("ethereum", "solana" 등)
	•	dst_chain = 받을 쪽 체인 ("hyperliquid")
	•	asset = 코인 ("eth", "sol")
	•	dst_addr = Hyperliquid(이더리움) 지갑 주소(즉, 위에서 생성한 address)
    '''
    # ETH 입금주소 생성 GET https://api.hyperunit.xyz/gen/ethereum/hyperliquid/eth/0xYourHLAddress
    url = f"{settings.HYPERUNIT_API_URL}/gen/ethereum/hyperliquid/eth/{account.address}"
    response = httpx.get(url)
    response.raise_for_status()
    '''
    ETH: {
        address: "0x3F344...",
        signatures: {
            field-node: "A/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
            hl-node: "roOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
            unit-node: "JO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
        },
        status: "OK"
    }
    '''
    eth_data = response.json()
    print(f"ETH deposit address generated: {eth_data['address']}")

    # ETH 서명 검증 (새로운 상세 검증 로직 사용)
    eth_proposal = Proposal(
        destination_address=account.address,
        destination_chain="hyperliquid",
        asset="eth",
        address=eth_data["address"],
        source_chain="ethereum"
    )
    
    # eth_verification_result = verify_deposit_address_signatures(
    #     signatures=eth_data["signatures"],
    #     proposal=eth_proposal
    # )

    # if not eth_verification_result.success:
    #     error_detail = f"ETH 입금 주소 생성 실패: {eth_verification_result.verified_count}/2 서명 검증됨"
    #     if eth_verification_result.errors:
    #         error_detail += f", 에러: {', '.join(eth_verification_result.errors)}"
    #     if eth_verification_result.verification_details:
    #         error_detail += f", 검증 상세: {eth_verification_result.verification_details}"
    #     raise HTTPException(status_code=400, detail=error_detail)

    # print(f"ETH signatures verified successfully: {eth_verification_result.verified_count}/2 nodes")

    # SOL 입금 주소 생성 GET https://api.hyperunit.xyz/gen/solana/hyperliquid/sol/0xYourHLAddress
    url = f"{settings.HYPERUNIT_API_URL}/gen/solana/hyperliquid/sol/{account.address}"
    response = httpx.get(url)
    response.raise_for_status()
    sol_data = response.json()
    print(f"SOL deposit address generated: {sol_data['address']}")

    # SOL 서명 검증 (새로운 상세 검증 로직 사용)
    sol_proposal = Proposal(
        destination_address=account.address,
        destination_chain="hyperliquid",
        asset="sol",
        address=sol_data["address"],
        source_chain="solana"
    )
    
    # sol_verification_result = verify_deposit_address_signatures(
    #     signatures=sol_data["signatures"],
    #     proposal=sol_proposal
    # )

    # if not sol_verification_result.success:
    #     error_detail = f"SOL 입금 주소 생성 실패: {sol_verification_result.verified_count}/2 서명 검증됨"
    #     if sol_verification_result.errors:
    #         error_detail += f", 에러: {', '.join(sol_verification_result.errors)}"
    #     if sol_verification_result.verification_details:
    #         error_detail += f", 검증 상세: {sol_verification_result.verification_details}"
    #     raise HTTPException(status_code=400, detail=error_detail)

    # print(f"SOL signatures verified successfully: {sol_verification_result.verified_count}/2 nodes")

    return {
       "wallet": {"address": account.address,
        "private_key": account.key.hex()},
        "deposit_address": {
            "ETH": eth_data,
            "SOL": sol_data
        }
    }

@router.post("/place_order")
async def place_order(order: OrderRequest):
    """
    HyperUnit을 통한 주문 실행 (Long/Short 포지션)
    
    - symbol: 거래할 심볼 (예: "BTC", "ETH")
    - side: "buy" (Long 포지션), "sell" (Short 포지션)
    - size: 포지션 크기 (USD)
    - price: 지정가 주문시 가격 (시장가 주문시 생략)
    - order_type: "market" (시장가) 또는 "limit" (지정가)
    """
    try:
        # 1. 주문 유효성 검증
        if order.side not in ["buy", "sell"]:
            raise HTTPException(status_code=400, detail="side must be 'buy' or 'sell'")
        
        if order.order_type not in ["market", "limit"]:
            raise HTTPException(status_code=400, detail="order_type must be 'market' or 'limit'")
        
        if order.order_type == "limit" and not order.price:
            raise HTTPException(status_code=400, detail="price is required for limit orders")
        
        # 2. 실제 Hyperliquid API를 통한 주문 실행
        # TODO: 실제 private_key는 보안상 별도로 관리해야 함
        # 현재는 목업 응답 반환
        
        return {
            "success": True,
            "order_id": f"order_{int(time.time())}",
            "symbol": order.symbol,
            "side": order.side,
            "size": order.size,
            "price": order.price,
            "order_type": order.order_type,
            "status": "submitted",
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement failed: {str(e)}")

@router.get("/positions/{address}")
async def get_positions(address: str):
    """
    특정 주소의 포지션 정보 조회
    
    - address: 조회할 지갑 주소
    """
    try:
        # 실제 Hyperliquid API를 통한 포지션 조회
        from app.core.hyperliquid_client import get_positions_real
        
        positions_data = await get_positions_real(address)
        return positions_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")

@router.get("/account/{address}")
async def get_account_info(address: str):
    """
    계정 정보 조회 (잔고, 마진 등)
    
    - address: 조회할 지갑 주소
    """
    try:
        # 실제 Hyperliquid API를 통한 계정 정보 조회
        from app.core.hyperliquid_client import get_account_info_real
        
        account_info = await get_account_info_real(address)
        return account_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch account info: {str(e)}")

@router.get("/open_orders/{address}")
async def get_open_orders(address: str):
    """
    오픈 오더 조회
    
    - address: 조회할 지갑 주소
    """
    try:
        # 실제 Hyperliquid API를 통한 오픈 오더 조회
        from app.core.hyperliquid_client import get_open_orders
        
        open_orders = await get_open_orders(address)
        return open_orders
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch open orders: {str(e)}")

@router.post("/close_position")
async def close_position(request: ClosePositionRequest):
    """
    포지션 종료 (비율 기반)
    
    - symbol: 종료할 포지션의 심볼
    - address: 지갑 주소
    - side: "long" 또는 "short" (생략시 모든 포지션 종료)
    - ratio: 종료할 비율 (0.0 ~ 1.0, 기본값: 1.0 = 전체 종료)
    - price: 지정가 종료시 가격 (시장가 종료시 생략)
    - order_type: "market" 또는 "limit"
    """
    try:
        # 1. 입력 유효성 검증
        if request.ratio < 0.0 or request.ratio > 1.0:
            raise HTTPException(status_code=400, detail="ratio must be between 0.0 and 1.0")
        
        if request.order_type not in ["market", "limit"]:
            raise HTTPException(status_code=400, detail="order_type must be 'market' or 'limit'")
        
        if request.order_type == "limit" and not request.price:
            raise HTTPException(status_code=400, detail="price is required for limit orders")
        
        if request.side and request.side not in ["long", "short"]:
            raise HTTPException(status_code=400, detail="side must be 'long' or 'short'")
        
        # 2. 실제 Hyperliquid API를 통한 포지션 종료
        from app.core.hyperliquid_client import close_position_real
        
        result = await close_position_real(
            address=request.address,
            symbol=request.symbol,
            side=request.side,
            ratio=request.ratio,
            price=request.price,
            order_type=request.order_type
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close position: {str(e)}")

@router.get("/order_history/{address}")
async def get_order_history(address: str, limit: int = 50):
    """
    주문 내역 조회
    
    - address: 지갑 주소
    - limit: 조회할 주문 수 (기본값: 50)
    """
    try:
        # TODO: 실제 주문 내역 조회 구현
        
        mock_orders = [
            {
                "order_id": "order_123",
                "symbol": "BTC",
                "side": "buy",
                "size": 1000.0,
                "price": 108000.0,
                "order_type": "market",
                "status": "filled",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ]
        
        return {
            "address": address,
            "orders": mock_orders,
            "total_count": len(mock_orders)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch order history: {str(e)}")