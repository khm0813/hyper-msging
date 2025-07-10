from fastapi import APIRouter, HTTPException
import httpx
from web3 import Web3, Account
from app.config import settings
from app.core.hyperunit_client import verify_signatures


router = APIRouter()

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
	•	src_chain = 자산이 존재하는 체인 (“ethereum”, “solana” 등)
	•	dst_chain = 받을 쪽 체인 (“hyperliquid”)
	•	asset = 코인 (“eth”, “sol”)
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

    # eth 서명 검증
    verified = verify_signatures(
        protocol_address=eth_data["address"],
        destination_address=account.address,
        destination_chain="hyperliquid",
        asset="eth",
        source_chain="ethereum",
        deposit_or_withdraw="deposit",
        signatures=eth_data["signatures"],  
    )

    if not verified:
        raise HTTPException(status_code=400, detail="ETH 입금 주소 생성 실패")

    # SOL 입금 주소 생성 GET https://api.hyperunit.xyz/gen/solana/hyperliquid/sol/0xYourHLAddress
    url = f"{settings.HYPERUNIT_API_URL}/gen/solana/hyperliquid/sol/{account.address}"
    response = httpx.get(url)
    response.raise_for_status()
    sol_data = response.json()

    # sol 서명 검증
    verified = verify_signatures(
        protocol_address=sol_data["address"],
        destination_address=account.address,
        destination_chain="hyperliquid",
        asset="sol",
        source_chain="solana",
        deposit_or_withdraw="deposit",
        signatures=sol_data["signatures"],  
    )

    if not verified:
        raise HTTPException(status_code=400, detail="SOL 입금 주소 생성 실패")

    return {
       "wallet": {"address": account.address,
        "private_key": account.key.hex()},
        "deposit_address": {
            "ETH": eth_data,
            "SOL": sol_data
        }
    }