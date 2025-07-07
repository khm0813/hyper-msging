import httpx
from app.config import settings
import hashlib

PRECOMPILE_ADDR = "0x0000000000000000000000000000000000000807"
DECIMALS = 6

async def get_price(market_id: int) -> float:
    # 실제 RPC 통신 대신, config의 HYPERLIQUID_API_ADDRESS와 market_id를 조합해 가짜 데이터 생성
    key = f"{market_id}:{settings.HYPERLIQUID_API_ADDRESS}:{settings.HYPERLIQUID_API_PRIVATE}"
    hash_val = hashlib.sha256(key.encode()).hexdigest()
    fake_price = int(hash_val[:8], 16) % 100_0000 / 10**DECIMALS
    return fake_price