#!/usr/bin/env python3
"""
실제 Hyperliquid API를 사용한 포지션 종료 테스트 스크립트
"""

import asyncio
import json
from app.core.hyperliquid_client import close_position_real, get_positions_real

async def test_real_close_position():
    """실제 포지션 종료 테스트"""
    
    address = "0x208546F8bca93fCb99afc382CB2abA829aFE9fD5"
    symbol = "BTC"
    
    print(f"테스트 주소: {address}")
    print(f"테스트 심볼: {symbol}")
    print("-" * 50)
    
    try:
        # 1. 현재 포지션 확인
        print("1. 현재 포지션 확인 중...")
        positions_data = await get_positions_real(address)
        print("현재 포지션:")
        for pos in positions_data["positions"]:
            print(f"  - {pos['symbol']} {pos['side']}: {pos['size']} @ {pos['entry_price']}")
            print(f"    미실현손익: {pos['unrealized_pnl']}")
        
        if not positions_data["positions"]:
            print("포지션이 없습니다. 테스트를 종료합니다.")
            return
        
        # 2. 25% 비율로 포지션 종료 테스트 (실제 API 호출)
        print("\n2. 25% 비율로 포지션 종료 테스트 (실제 API 호출)...")
        close_result = await close_position_real(
            address=address,
            symbol=symbol,
            side="short",  # 현재 short 포지션이 있음
            ratio=0.25,    # 25% 종료
            order_type="market"
        )
        
        print("종료 결과:")
        print(json.dumps(close_result, indent=2))
        
        # 3. API 응답 상세 확인
        if close_result.get("orders"):
            print("\n3. API 응답 상세:")
            for order in close_result["orders"]:
                print(f"  주문 ID: {order['order_id']}")
                print(f"  상태: {order['status']}")
                if "api_response" in order:
                    print(f"  API 응답: {json.dumps(order['api_response'], indent=4)}")
                if "error" in order:
                    print(f"  오류: {order['error']}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_close_position()) 