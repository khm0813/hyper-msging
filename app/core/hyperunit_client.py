import base64
import hashlib
from eth_keys.datatypes import PublicKey, Signature

# Hyperunit 공식 가디언 공개키 (예시는 테스트넷 기준, 메인넷은 공식문서 참고)
GUARDIAN_PUBLIC_KEYS = {
    'field-node': '04ae2ab20787f816ea5d13f36c4c4f7e196e29e867086f3ce818abb73077a237f841b33ada5be71b83f4af29f333dedc5411ca4016bd52ab657db2896ef374ce99', 
    'hl-node': '048633ea6ab7e40cdacf37d1340057e84bb9810de0687af78d031e9b07b65ad4ab379180ab55075f5c2ebb96dab30d2c2fab49d5635845327b6a3c27d20ba4755b', 
    'unit-node': '04dc6f89f921dc816aa69b687be1fcc3cc1d48912629abc2c9964e807422e1047e0435cb5ba0fa53cb9a57a9c610b4e872a0a2caedda78c4f85ebafcca93524061'
}
def make_hyperunit_payload(node_id, destination_address, destination_chain, asset, protocol_address, source_chain, deposit_or_withdraw):
    return f"{node_id}:{destination_address}-{destination_chain}-{asset}-{protocol_address}-{source_chain}-{deposit_or_withdraw}"

def verify_signatures(
    protocol_address: str,
    destination_address: str,
    destination_chain: str,
    asset: str,
    source_chain: str,
    deposit_or_withdraw: str,
    signatures: dict,
    guardian_public_keys: dict = GUARDIAN_PUBLIC_KEYS
) -> bool:
    verified = 0
    for node_id, pubkey_hex in guardian_public_keys.items():
        signature_b64 = signatures.get(node_id)
        if not signature_b64:
            continue
        try:
            signature_bytes = base64.b64decode(signature_b64)
            payload = make_hyperunit_payload(
                node_id,
                destination_address,
                destination_chain,
                asset,
                protocol_address,
                source_chain,
                deposit_or_withdraw
            )
            payload_hash = hashlib.sha256(payload.encode()).digest()
            public_key = PublicKey(bytes.fromhex(pubkey_hex))
            # signature_bytes는 r(32)+s(32)+v(1)일 수 있음, v 값 필요없으면 64바이트만 사용
            if len(signature_bytes) == 65:
                signature_bytes = signature_bytes[:64]
            # Signature 객체 생성하여 verify_msg_hash에 전달
            signature = Signature(signature_bytes)
            if public_key.verify_msg_hash(payload_hash, signature):
                verified += 1
        except Exception as e:
            continue
    return verified >= 2  # 2개 이상 성공시 True

# 사용 예시
# from utils import verify_signatures
# is_valid = verify_signatures(
#     protocol_address=...,
#     destination_address=...,
#     destination_chain=...,
#     asset=...,
#     source_chain=...,
#     deposit_or_withdraw="deposit",
#     signatures=...  # dict형식
# )