#!/usr/bin/env python3
"""
Hyperliquid API 디버그 스크립트
"""

import asyncio
import httpx
import json
from app.config import settings

async def debug_hyperliquid_api():
    """Hyperliquid API 요청 형식 디버그"""
    
    print("=== Hyperliquid API 디버그 ===\n")
    
    # 1. 가장 기본적인 API 테스트 (사용자 정보 없이)
    print("1. 기본 API 테스트 (사용자 정보 없이)...")
    
    basic_payloads = [
        {"type": "meta"},
        {"type": "allMids"},
        {"type": "openOrders"},
        {"type": "clearinghouseState"},
        {"type": "userState"},
        {"type": "userInfo"},
        {"type": "accountState"},
        {"type": "positions"},
    ]
    
    url = f"{settings.HYPERLIQUID_API_URL}/info"
    
    for i, payload in enumerate(basic_payloads):
        print(f"\n기본 테스트 {i+1}: {payload}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"Success! Response: {json.dumps(result, indent=2)[:500]}...")
                else:
                    print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")
    
    print("\n" + "="*50)
    
    # 2. 사용자 정보가 필요한 API 테스트
    print("\n2. 사용자 정보가 필요한 API 테스트...")
    
    # 테스트 주소 (정규화된 형식)
    test_address = "0x2329dac374d63a8bc515664cb8f8fe8d388942259fd8ad48bae8___"
    normalized_address = test_address.lower().replace("0x", "")
    
    print(f"원본 주소: {test_address}")
    print(f"정규화된 주소: {normalized_address}")
    
    # 사용자 정보가 필요한 API들
    user_payloads = [
        {"type": "clearinghouseState", "user": normalized_address},
        {"type": "openOrders", "user": normalized_address},
        {"type": "userState", "user": normalized_address},
        {"type": "userInfo", "user": normalized_address},
        {"type": "accountState", "user": normalized_address},
        {"type": "positions", "user": normalized_address},
    ]
    
    for i, payload in enumerate(user_payloads):
        print(f"\n사용자 테스트 {i+1}: {payload}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"Success! Response: {json.dumps(result, indent=2)[:500]}...")
                else:
                    print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")
    
    print("\n" + "="*50)
    
    # 3. 다른 API 엔드포인트 테스트
    print("\n3. 다른 API 엔드포인트 테스트...")
    
    # exchange API 테스트
    print("\nExchange API 테스트...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{settings.HYPERLIQUID_API_URL}/exchange", 
                                       json={"action": "ping"})
            print(f"Exchange API Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Exchange API Response: {json.dumps(result, indent=2)[:500]}...")
            else:
                print(f"Exchange API Error: {response.text}")
    except Exception as e:
        print(f"Exchange API Exception: {e}")
    
    # 4. GET 요청 테스트
    print("\n4. GET 요청 테스트...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.HYPERLIQUID_API_URL}/info")
            print(f"GET Info Status: {response.status_code}")
            if response.status_code == 200:
                result = response.text
                print(f"GET Info Response: {result[:500]}...")
            else:
                print(f"GET Info Error: {response.text}")
    except Exception as e:
        print(f"GET Info Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_hyperliquid_api()) 