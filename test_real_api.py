#!/usr/bin/env python3
"""
실제 Hyperliquid API 포지션 종료(close) 테스트
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.hyperliquid_client import (
    get_positions_real,
    close_position_real
)
from app.config import settings

async def test_close_position():
    print("=== Hyperliquid API 포지션 종료 테스트 ===\n")
    private_key = settings.TEST_PRIVATE_KEY
    address = "0x208546F8bca93fCb99afc382CB2abA829aFE9fD5"

    # 1. 포지션 조회
    print("1. 포지션 조회...")
    try:
        positions = await get_positions_real(address)
        print(f"포지션 정보: {positions}")
    except Exception as e:
        print(f"포지션 조회 중 예외 발생: {e}")
        import traceback; traceback.print_exc()
        return

    # 2. BTC/short 포지션이 있으면 종료
    pos_list = positions.get("positions") if isinstance(positions, dict) else None
    target = None
    if pos_list:
        for pos in pos_list:
            if pos["symbol"] == "BTC" and pos["side"] == "short":
                target = pos
                break
    if target:
        print(f"\n2. BTC/short 포지션 종료 시도: {target}")
        try:
            close_result = await close_position_real(
                address=address,
                symbol="BTC",
                side="short",
                ratio=1.0,  # 전량 종료
                order_type="market"
            )
            print(f"포지션 종료 결과: {close_result}")
        except Exception as e:
            print(f"포지션 종료 중 예외 발생: {e}")
            import traceback; traceback.print_exc()
    else:
        print("BTC/short 포지션이 없습니다. 테스트 종료.")

if __name__ == "__main__":
    asyncio.run(test_close_position()) 