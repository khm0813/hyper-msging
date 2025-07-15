from hyperliquid import HyperliquidAsync
from app.config import settings
from typing import Optional

# HyperliquidAsync 인스턴스 생성 (최신 SDK 방식)
client = HyperliquidAsync({
    "walletAddress": settings.HYPERLIQUID_API_ADDRESS,
    "privateKey": settings.HYPERLIQUID_API_PRIVATE,
    "base_url": settings.HYPERLIQUID_API_URL
})

async def get_mark_price(symbol: str) -> float:
    """
    심볼의 마크 가격(mark price)을 Hyperliquid public_post_info로 조회
    """
    req = {
        'type': 'metaAndAssetCtxs'
    }
    data = await client.public_post_info(req)
    # universe와 assetCtxs 구조에서 심볼 인덱스 찾기
    universe = data[0]['universe']
    asset_ctxs = data[1]
    for idx, asset in enumerate(universe):
        if asset['name'] == symbol:
            return float(asset_ctxs[idx]['markPx'])
    raise Exception(f"Mark price not found for {symbol}")

async def place_long(symbol: str, size: float):
    """롱(매수) 포지션 오픈 (시장가)"""
    market = f"{symbol}/USDC:USDC"
    mark_price = await get_mark_price(symbol)
    resp = await client.create_market_order(
        market,
        "buy",
        size,
        price=mark_price
    )
    print("롱 주문 결과:", resp)
    return resp

async def place_short(symbol: str, size: float):
    """숏(매도) 포지션 오픈 (시장가)"""
    market = f"{symbol}/USDC:USDC"
    mark_price = await get_mark_price(symbol)
    resp = await client.create_market_order(
        market,
        "sell",
        size,
        price=mark_price
    )
    print("숏 주문 결과:", resp)
    return resp

async def close_position_real(
    address: str,
    symbol: str,
    side: Optional[str] = None,
    ratio: float = 1.0,
    price: float = 0.0,
    order_type: str = "market"
) -> dict:
    """
    HyperliquidAsync SDK 기반으로 포지션 종료 (비율 기반)
    address 인자는 현재 SDK에서는 사용하지 않음 (agent_wallet 기준)
    """
    market = f"{symbol}/USDC:USDC"
    # 1. 포지션 정보 조회 (최신 SDK)
    positions = await client.fetch_positions([market], params={"user": address})
    target_positions = []
    for pos in positions:
        if pos["symbol"] == market:
            # side가 None, 빈 문자열, 또는 일치하는 경우 모두 허용
            if not side or pos["side"] == side:
                target_positions.append(pos)
    if not target_positions:
        raise Exception(f"No position found for {symbol} {side if side else ''}")
    close_orders = []
    for pos in target_positions:
        close_size = float(pos["contracts"] if "contracts" in pos else pos.get("size", 0)) * ratio
        if close_size > 0:
            close_side = "sell" if pos["side"] == "long" else "buy"
            close_orders.append({
                "market": market,
                "side": close_side,
                "size": close_size
            })
    executed_orders = []
    for order in close_orders:
        try:
            # 시장가 주문 시 마크 가격을 price로 사용
            mark_price = await get_mark_price(symbol)
            if order_type == "limit":
                resp = await client.create_limit_order(
                    order["market"],
                    "limit",
                    order["side"],
                    order["size"],
                    price
                )
            else:
                resp = await client.create_market_order(
                    order["market"],
                    order["side"],
                    order["size"],
                    price=mark_price
                )
            # 체결 여부를 filled 정보로 판단
            is_filled = (
                resp.get("status") == "filled"
                or ("info" in resp and isinstance(resp["info"], dict) and "filled" in resp["info"]))
            executed_order = {
                "order_id": resp.get("order_id", f"close_{order['market']}_{order['side']}_{order['size']}"),
                "market": order["market"],
                "side": order["side"],
                "size": order["size"],
                "status": "filled" if is_filled else resp.get("status", "submitted"),
                "api_response": resp
            }
        except Exception as e:
            executed_order = {
                "order_id": f"error_{order['market']}_{order['side']}_{order['size']}",
                "market": order["market"],
                "side": order["side"],
                "size": order["size"],
                "status": "failed",
                "error": str(e)
            }
        executed_orders.append(executed_order)
    return {
        "success": all(o["status"] == "filled" for o in executed_orders),
        "symbol": symbol,
        "side": side,
        "ratio": ratio,
        "orders": executed_orders,
        "total_closed_size": sum(float(order["size"]) for order in close_orders),
        "status": "filled" if all(o["status"] == "filled" for o in executed_orders) else "failed",
        "message": f"Position close orders submitted for {symbol}"
    } 