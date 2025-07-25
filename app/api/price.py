from fastapi import APIRouter, HTTPException
import httpx
from app.core.hyperevm_client import get_price, get_orderbook, get_symbols, is_valid_symbol, get_asset_ctx

router = APIRouter()

@router.get("/symbols")
async def read_symbols():
    symbols = await get_symbols()
    return {"symbols": symbols}

@router.get("/orderbook/{symbol}")
async def read_orderbook(symbol: str):
    print(symbol)
    if not symbol or not symbol.isalnum():
        raise HTTPException(status_code=400, detail="Invalid symbol")
    if not await is_valid_symbol(symbol):
        raise HTTPException(status_code=404, detail=f"Symbol not found: {symbol}")
    try:
        result = await get_orderbook(symbol)
        if not result["bids"] and not result["asks"]:
            raise HTTPException(status_code=404, detail=f"Orderbook not found for symbol: {symbol}")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream RPC error")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result

@router.get("/asset_ctx/{symbol}")
async def read_asset_ctx(symbol: str):
    """
    심볼별 트레이딩 주요 지표(컨텍스트) 정보를 반환하는 엔드포인트
    - symbol: 코인 심볼 (예: BTC)
    - 반환: funding, openInterest, markPx, midPx, oraclePx, premium, prevDayPx, dayNtlVlm, impactPxs, dayBaseVlm 등
    - 404: 존재하지 않는 심볼
    - 502: Upstream API 오류
    - 400: 기타 오류
    """
    if not symbol or not symbol.isalnum():
        raise HTTPException(status_code=400, detail="Invalid symbol")
    if not await is_valid_symbol(symbol):
        raise HTTPException(status_code=404, detail=f"Symbol not found: {symbol}")
    try:
        result = await get_asset_ctx(symbol)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream RPC error")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result

@router.get("/{market_id}")
async def read_price(market_id: int):
    if market_id < 0:
        raise HTTPException(status_code=400, detail="market_id must be non-negative")
    try:
        result = await get_price(market_id)
        # 심볼 유효성 검증
        if not await is_valid_symbol(result["symbol"]):
            raise HTTPException(status_code=404, detail=f"Symbol not found: {result['symbol']}")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream RPC error")
    return {"market_id": market_id, "symbol": result["symbol"], "price": result["price"]}