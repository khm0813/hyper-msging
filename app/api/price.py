from fastapi import APIRouter, HTTPException
import httpx
from app.core.hyperevm_client import get_price

router = APIRouter()

@router.get("/{market_id}")
async def read_price(market_id: int):
    if market_id < 0:
        raise HTTPException(status_code=400, detail="market_id must be non-negative")
    try:
        result = await get_price(market_id)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream RPC error")
    return {"market_id": market_id, "symbol": result["symbol"], "price": result["price"]}