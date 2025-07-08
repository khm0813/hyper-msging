import httpx
from app.config import settings
import hashlib
from typing import Dict, List

PRECOMPILE_ADDR = "0x0000000000000000000000000000000000000807"
DECIMALS = 6

# 마켓 ID -> 코인 심볼 매핑을 위한 캐시 (최초 1회만 요청)
_market_id_to_symbol: Dict[int, str] = {}

async def _fetch_market_meta() -> None:
    global _market_id_to_symbol
    url = f"{settings.HYPERLIQUID_API_URL}/info"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"type": "meta"})
        resp.raise_for_status()
        data = resp.json()
        # universe: List[Dict] with 'name' and 'index' (index는 0부터 순서)
        universe: List[dict] = data.get("universe", [])
        _market_id_to_symbol = {i: asset["name"] for i, asset in enumerate(universe)}
        print(_market_id_to_symbol)

async def get_price(market_id: int) -> dict:
    # 1. 마켓 ID -> 코인 심볼 매핑 (최초 1회만 meta 호출)
    if not _market_id_to_symbol:
        await _fetch_market_meta()
    symbol = _market_id_to_symbol.get(market_id)
    if not symbol:
        raise ValueError(f"Invalid market_id: {market_id}")
    # 2. 가격 전체 조회
    url = f"{settings.HYPERLIQUID_API_URL}/info"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"type": "allMids"})
        resp.raise_for_status()
        mids = resp.json()  # {"BTC": "69123.5", ...}
    price_str = mids.get(symbol)
    if price_str is None:
        raise ValueError(f"Price not found for symbol: {symbol}")
    return {"symbol": symbol, "price": float(price_str)}