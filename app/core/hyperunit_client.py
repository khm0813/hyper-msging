import base64
import hashlib
from typing import Dict, Optional, List
from dataclasses import dataclass
from eth_keys.datatypes import PublicKey, Signature

# 메인넷/테스트넷 가디언 노드 공개키 (필요시 둘 다 선언)
MAINNET_GUARDIAN_NODES = {
    'unit-node': '04dc6f89f921dc816aa69b687be1fcc3cc1d48912629abc2c9964e807422e1047e0435cb5ba0fa53cb9a57a9c610b4e872a0a2caedda78c4f85ebafcca93524061',
    'hl-node': '048633ea6ab7e40cdacf37d1340057e84bb9810de0687af78d031e9b07b65ad4ab379180ab55075f5c2ebb96dab30d2c2fab49d5635845327b6a3c27d20ba4755b',
    'field-node': '04ae2ab20787f816ea5d13f36c4c4f7e196e29e867086f3ce818abb73077a237f841b33ada5be71b83f4af29f333dedc5411ca4016bd52ab657db2896ef374ce99'
}

GUARDIAN_SIGNATURE_THRESHOLD = 2

@dataclass
class Proposal:
    destination_address: str
    destination_chain: str
    asset: str
    address: str  # protocol_address
    source_chain: str
    coin_type: Optional[str] = None
    key_type: Optional[str] = None

@dataclass
class VerificationResult:
    success: bool
    verified_count: int
    errors: Optional[List[str]] = None
    verification_details: Optional[Dict[str, bool]] = None

def hex_to_bytes(hex_string: str) -> bytes:
    clean_hex = hex_string[2:] if hex_string.startswith('0x') else hex_string
    return bytes.fromhex(clean_hex)

def legacy_proposal_to_payload(node_id: str, proposal: Proposal) -> bytes:
    # 예전(Hyperunit v1) 방식
    payload_string = f"{node_id}:{proposal.destination_address}-{proposal.destination_chain}-{proposal.asset}-{proposal.address}-{proposal.source_chain}-deposit"
    return payload_string.encode('utf-8')

def new_proposal_to_payload(node_id: str, proposal: Proposal) -> bytes:
    # 새로운(Hyperunit v2, 이더리움 등) 방식
    payload_string = f"{node_id}:user-{proposal.coin_type}-{proposal.destination_chain}-{proposal.destination_address}-{proposal.address}"
    return payload_string.encode('utf-8')

def proposal_to_payload(node_id: str, proposal: Proposal) -> bytes:
    if proposal.coin_type == 'ethereum':
        return new_proposal_to_payload(node_id, proposal)
    return legacy_proposal_to_payload(node_id, proposal)

def process_guardian_nodes(guardian_nodes: Dict[str, str]) -> Dict[str, PublicKey]:
    processed_nodes = {}
    for node_id, public_key_hex in guardian_nodes.items():
        # 04 prefix 제거 (eth_keys는 64바이트 기대)
        pubkey = public_key_hex[2:] if public_key_hex.startswith('04') else public_key_hex
        public_key_bytes = bytes.fromhex(pubkey)
        if len(public_key_bytes) != 64:
            raise ValueError(f"Invalid public key length for node {node_id}: {len(public_key_bytes)} bytes")
        public_key = PublicKey(public_key_bytes)
        processed_nodes[node_id] = public_key
    return processed_nodes

def verify_signature(public_key: PublicKey, message: bytes, signature_b64: str) -> bool:
    try:
        signature_bytes = base64.b64decode(signature_b64)
        
        # 서명 길이 검증
        if len(signature_bytes) not in [64, 65]:
            print(f"Invalid signature length: {len(signature_bytes)} bytes")
            return False
        
        # 64바이트 서명인 경우 v 값 추가
        if len(signature_bytes) == 64:
            signature_bytes = signature_bytes + b'\x00'  # v=0
        
        # v 값이 27 이상인 경우 27을 빼서 실제 v 값으로 변환
        if len(signature_bytes) == 65 and signature_bytes[64] >= 27:
            signature_bytes = signature_bytes[:64] + bytes([signature_bytes[64] - 27])
        
        message_hash = hashlib.sha256(message).digest()
        signature = Signature(signature_bytes)
        
        result = public_key.verify_msg_hash(message_hash, signature)
        return result
        
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False

def verify_deposit_address_signatures(
    signatures: Dict[str, str],
    proposal: Proposal,
    guardian_nodes: Optional[Dict[str, str]] = None,
    threshold: int = GUARDIAN_SIGNATURE_THRESHOLD
) -> VerificationResult:
    if guardian_nodes is None:
        guardian_nodes = MAINNET_GUARDIAN_NODES

    try:
        processed_nodes = process_guardian_nodes(guardian_nodes)
        verified_count = 0
        errors = []
        verification_details = {}

        for node_id, public_key in processed_nodes.items():
            try:
                if node_id not in signatures:
                    verification_details[node_id] = False
                    continue

                is_verified = False

                # coin_type이 ethereum이 아니면 레거시/신규 페이로드 모두 시도
                if proposal.coin_type != 'ethereum':
                    legacy_payload = legacy_proposal_to_payload(node_id, proposal)
                    print('legacy_payload', legacy_payload)
                    is_verified = verify_signature(public_key, legacy_payload, signatures[node_id])
                    print('is_verified', is_verified)
                    if not is_verified:
                        new_payload = new_proposal_to_payload(node_id, proposal)
                        is_verified = verify_signature(public_key, new_payload, signatures[node_id])
                else:
                    payload = new_proposal_to_payload(node_id, proposal)
                    print('payload', payload)
                    is_verified = verify_signature(public_key, payload, signatures[node_id])
                    print('is_verified', is_verified)

                

                verification_details[node_id] = is_verified
                if is_verified:
                    verified_count += 1

            except Exception as e:
                errors.append(f"Verification failed for node {node_id}: {str(e)}")
                verification_details[node_id] = False

        return VerificationResult(
            success=verified_count >= threshold,
            verified_count=verified_count,
            errors=errors if errors else None,
            verification_details=verification_details
        )

    except Exception as e:
        return VerificationResult(
            success=False,
            verified_count=0,
            errors=[f"Global verification error: {str(e)}"],
            verification_details={}
        )

# 래퍼 함수: 기존 verify_signatures 패턴 호환
def verify_signatures(
    protocol_address: str,
    destination_address: str,
    destination_chain: str,
    asset: str,
    source_chain: str,
    deposit_or_withdraw: str,
    signatures: Dict[str, str],
    coin_type: Optional[str] = None,
    guardian_nodes: Optional[Dict[str, str]] = None,
    threshold: int = GUARDIAN_SIGNATURE_THRESHOLD
) -> bool:
    proposal = Proposal(
        destination_address=destination_address,
        destination_chain=destination_chain,
        asset=asset,
        address=protocol_address,
        source_chain=source_chain,
        coin_type=coin_type
    )
    result = verify_deposit_address_signatures(signatures, proposal, guardian_nodes, threshold)
    return result.success

# 필요시 payload 생성 유틸
def make_hyperunit_payload(node_id: str, destination_address: str, destination_chain: str,
                          asset: str, protocol_address: str, source_chain: str, deposit_or_withdraw: str) -> str:
    proposal = Proposal(
        destination_address=destination_address,
        destination_chain=destination_chain,
        asset=asset,
        address=protocol_address,
        source_chain=source_chain
    )
    payload_bytes = legacy_proposal_to_payload(node_id, proposal)
    return payload_bytes.decode('utf-8')