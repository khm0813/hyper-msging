import httpx
from app.config import settings
import hashlib
from typing import Dict, List
import asyncio
import time

PRECOMPILE_ADDR = "0x0000000000000000000000000000000000000807"
DECIMALS = 6

# 마켓 ID -> 코인 심볼 매핑을 위한 캐시 (최초 1회만 요청)
_market_id_to_symbol: Dict[int, str] = {}
_symbol_list: List[str] = []
_symbols_last_fetched: float = 0
_symbols_lock = asyncio.Lock()
_SYMBOLS_CACHE_TTL = 300  # 5분

async def _fetch_market_meta() -> None:
    global _market_id_to_symbol, _symbol_list, _symbols_last_fetched
    url = f"{settings.HYPERLIQUID_API_URL}/info"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"type": "meta"})
        resp.raise_for_status()
        data = resp.json()
        universe: List[dict] = data.get("universe", [])
        _market_id_to_symbol = {i: asset["name"] for i, asset in enumerate(universe)}
        _symbol_list = [asset["name"] for asset in universe]
        _symbols_last_fetched = time.time()

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

async def get_orderbook(symbol: str) -> dict:
    """
    Hypeliquid에서 심볼별 오더북(호가) 정보를 조회한다.
    반환 예시: {"symbol": symbol, "bids": [[가격, 수량], ...], "asks": [[가격, 수량], ...]}
    """
    url = f"{settings.HYPERLIQUID_API_URL}/info"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"type": "l2Book", "coin": symbol})
        resp.raise_for_status()
        data = resp.json()
        print("get_orderbook", data)
        # data['levels']는 [bids, asks] 리스트 구조임
        '''
        {
            "coin": "BTC",
            "time": ...,
            "levels": [
                [ ...bids... ],  // 0번 인덱스: 매수호가 리스트
                [ ...asks... ]   // 1번 인덱스: 매도호가 리스트
            ]
        }
        '''
        levels = data.get("levels", [[], []])
        bids = levels[0] if len(levels) > 0 else []
        asks = levels[1] if len(levels) > 1 else []
    return {"symbol": symbol, "bids": bids, "asks": asks}

async def get_symbols() -> List[str]:
    """
    Hypeliquid에서 거래 가능한 모든 심볼(코인명) 리스트를 반환한다. (5분 캐싱)
    """
    async with _symbols_lock:
        now = time.time()
        if not _symbol_list or now - _symbols_last_fetched > _SYMBOLS_CACHE_TTL:
            await _fetch_market_meta()
        return list(_symbol_list)

async def is_valid_symbol(symbol: str) -> bool:
    """
    현재 캐시된 심볼 리스트에 symbol이 존재하는지 확인한다. (비어 있으면 fetch)
    """
    if not _symbol_list:
        await get_symbols()
    return symbol in _symbol_list

async def get_asset_ctx(symbol: str) -> dict:
    """
    Hypeliquid에서 심볼별 트레이딩 주요 지표(컨텍스트) 정보를 조회한다.
    - symbol: 조회할 코인 심볼 (예: "BTC")
    - 반환 예시:
      {
        "symbol": "BTC",
        "funding": 0.0000125,
        "openInterest": 34345.24704,
        "markPx": 108889.0,
        "midPx": 108889.5,
        "oraclePx": 108859.0,
        "premium": 0.0002755858,
        "prevDayPx": 108232.0,
        "dayNtlVlm": 2138608387.4016401768,
        "impactPxs": [108889.0, 108890.0],
        "dayBaseVlm": 19671.09977
      }
    - symbol이 없으면 ValueError 발생
    """
    url = f"{settings.HYPERLIQUID_API_URL}/info"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"type": "metaAndAssetCtxs"})
        resp.raise_for_status()
        data = resp.json()
        universe = data[0]["universe"]
        asset_ctxs = data[1]
        symbol_to_idx = {asset["name"]: idx for idx, asset in enumerate(universe)}
        idx = symbol_to_idx.get(symbol)
        if idx is None:
            raise ValueError(f"Symbol not found: {symbol}")
        ctx = asset_ctxs[idx]
    # 필요한 필드만 float 변환 및 반환
    def f(x):
        try:
            return float(x)
        except Exception:
            return x
    return {
        "symbol": symbol,
        "funding": f(ctx.get("funding")),
        "openInterest": f(ctx.get("openInterest")),
        "markPx": f(ctx.get("markPx")),
        "midPx": f(ctx.get("midPx")),
        "oraclePx": f(ctx.get("oraclePx")),
        "premium": f(ctx.get("premium")),
        "prevDayPx": f(ctx.get("prevDayPx")),
        "dayNtlVlm": f(ctx.get("dayNtlVlm")),
        "impactPxs": [f(x) for x in ctx.get("impactPxs", [])],
        "dayBaseVlm": f(ctx.get("dayBaseVlm")),
    }