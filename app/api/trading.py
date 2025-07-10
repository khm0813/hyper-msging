from fastapi import APIRouter, HTTPException
import httpx
from web3 import Web3, Account
from app.config import settings
from app.core.hyperunit_client import verify_signatures, verify_deposit_address_signatures, Proposal


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
	•	src_chain = 자산이 존재하는 체인 ("ethereum", "solana" 등)
	•	dst_chain = 받을 쪽 체인 ("hyperliquid")
	•	asset = 코인 ("eth", "sol")
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
    print(f"ETH deposit address generated: {eth_data['address']}")

    # ETH 서명 검증 (새로운 상세 검증 로직 사용)
    eth_proposal = Proposal(
        destination_address=account.address,
        destination_chain="hyperliquid",
        asset="eth",
        address=eth_data["address"],
        source_chain="ethereum"
    )
    
    # eth_verification_result = verify_deposit_address_signatures(
    #     signatures=eth_data["signatures"],
    #     proposal=eth_proposal
    # )

    # if not eth_verification_result.success:
    #     error_detail = f"ETH 입금 주소 생성 실패: {eth_verification_result.verified_count}/2 서명 검증됨"
    #     if eth_verification_result.errors:
    #         error_detail += f", 에러: {', '.join(eth_verification_result.errors)}"
    #     if eth_verification_result.verification_details:
    #         error_detail += f", 검증 상세: {eth_verification_result.verification_details}"
    #     raise HTTPException(status_code=400, detail=error_detail)

    # print(f"ETH signatures verified successfully: {eth_verification_result.verified_count}/2 nodes")

    # SOL 입금 주소 생성 GET https://api.hyperunit.xyz/gen/solana/hyperliquid/sol/0xYourHLAddress
    url = f"{settings.HYPERUNIT_API_URL}/gen/solana/hyperliquid/sol/{account.address}"
    response = httpx.get(url)
    response.raise_for_status()
    sol_data = response.json()
    print(f"SOL deposit address generated: {sol_data['address']}")

    # SOL 서명 검증 (새로운 상세 검증 로직 사용)
    sol_proposal = Proposal(
        destination_address=account.address,
        destination_chain="hyperliquid",
        asset="sol",
        address=sol_data["address"],
        source_chain="solana"
    )
    
    # sol_verification_result = verify_deposit_address_signatures(
    #     signatures=sol_data["signatures"],
    #     proposal=sol_proposal
    # )

    # if not sol_verification_result.success:
    #     error_detail = f"SOL 입금 주소 생성 실패: {sol_verification_result.verified_count}/2 서명 검증됨"
    #     if sol_verification_result.errors:
    #         error_detail += f", 에러: {', '.join(sol_verification_result.errors)}"
    #     if sol_verification_result.verification_details:
    #         error_detail += f", 검증 상세: {sol_verification_result.verification_details}"
    #     raise HTTPException(status_code=400, detail=error_detail)

    # print(f"SOL signatures verified successfully: {sol_verification_result.verified_count}/2 nodes")

    return {
       "wallet": {"address": account.address,
        "private_key": account.key.hex()},
        "deposit_address": {
            "ETH": eth_data,
            "SOL": sol_data
        }
    }