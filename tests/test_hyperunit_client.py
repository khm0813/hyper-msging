import pytest
import base64
from app.core.hyperunit_client import (
    verify_signatures, 
    make_hyperunit_payload,
    verify_deposit_address_signatures,
    Proposal,
    VerificationResult,
    legacy_proposal_to_payload,
    new_proposal_to_payload,
    MAINNET_GUARDIAN_NODES
)

class TestHyperunitClient:
    """Hyperunit 클라이언트 테스트 클래스"""
    
    def test_make_hyperunit_payload(self):
        """페이로드 생성 함수 테스트"""
        payload = make_hyperunit_payload(
            node_id="field-node",
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            protocol_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            source_chain="polygon",
            deposit_or_withdraw="deposit"
        )
        
        expected = "field-node:0x1234567890123456789012345678901234567890-ethereum-USDC-0xabcdefabcdefabcdefabcdefabcdefabcdefabcd-polygon-deposit"
        assert payload == expected
    
    def test_legacy_proposal_to_payload(self):
        """레거시 페이로드 형식 테스트"""
        proposal = Proposal(
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            source_chain="polygon"
        )
        
        payload = legacy_proposal_to_payload("field-node", proposal)
        expected = b"field-node:0x1234567890123456789012345678901234567890-ethereum-USDC-0xabcdefabcdefabcdefabcdefabcdefabcdefabcd-polygon-deposit"
        assert payload == expected
    
    def test_new_proposal_to_payload(self):
        """새로운 페이로드 형식 테스트 (ethereum coin_type)"""
        proposal = Proposal(
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            source_chain="polygon",
            coin_type="ethereum"
        )
        
        payload = new_proposal_to_payload("field-node", proposal)
        expected = b"field-node:user-ethereum-ethereum-0x1234567890123456789012345678901234567890-0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
        assert payload == expected
    
    def test_verify_signatures_with_valid_data(self):
        """유효한 서명 데이터로 검증 테스트"""
        # 테스트용 더미 서명 (실제로는 유효한 서명이어야 함)
        test_signatures = {
            'field-node': base64.b64encode(b'0' * 64).decode(),
            'hl-node': base64.b64encode(b'0' * 64).decode(),
            'unit-node': base64.b64encode(b'0' * 64).decode()
        }
        
        # 이 테스트는 실제 유효한 서명이 아니므로 False를 반환할 것으로 예상
        result = verify_signatures(
            protocol_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            source_chain="polygon",
            deposit_or_withdraw="deposit",
            signatures=test_signatures
        )
        
        # 더미 서명이므로 False를 반환해야 함
        assert result == False
    
    def test_verify_deposit_address_signatures_with_legacy_format(self):
        """레거시 형식으로 서명 검증 테스트"""
        proposal = Proposal(
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            source_chain="polygon"
        )
        
        test_signatures = {
            'field-node': base64.b64encode(b'0' * 64).decode(),
            'hl-node': base64.b64encode(b'0' * 64).decode(),
            'unit-node': base64.b64encode(b'0' * 64).decode()
        }
        
        result = verify_deposit_address_signatures(test_signatures, proposal)
        
        assert isinstance(result, VerificationResult)
        assert result.success == False
        assert result.verified_count == 0
        assert result.verification_details is not None
        assert len(result.verification_details) == 3
    
    def test_verify_deposit_address_signatures_with_ethereum_format(self):
        """Ethereum 형식으로 서명 검증 테스트"""
        proposal = Proposal(
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            source_chain="polygon",
            coin_type="ethereum"
        )
        
        test_signatures = {
            'field-node': base64.b64encode(b'0' * 64).decode(),
            'hl-node': base64.b64encode(b'0' * 64).decode(),
            'unit-node': base64.b64encode(b'0' * 64).decode()
        }
        
        result = verify_deposit_address_signatures(test_signatures, proposal)
        
        assert isinstance(result, VerificationResult)
        assert result.success == False
        assert result.verified_count == 0
    
    def test_verify_signatures_with_missing_signatures(self):
        """서명이 누락된 경우 테스트"""
        test_signatures = {
            'field-node': base64.b64encode(b'0' * 64).decode(),
            # 'hl-node'와 'unit-node' 서명 누락
        }
        
        result = verify_signatures(
            protocol_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            source_chain="polygon",
            deposit_or_withdraw="deposit",
            signatures=test_signatures
        )
        
        # 2개 이상의 서명이 필요하므로 False를 반환해야 함
        assert result == False
    
    def test_verify_signatures_with_empty_signatures(self):
        """빈 서명 딕셔너리 테스트"""
        result = verify_signatures(
            protocol_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            source_chain="polygon",
            deposit_or_withdraw="deposit",
            signatures={}
        )
        
        assert result == False
    
    def test_mainnet_guardian_nodes_structure(self):
        """메인넷 가디언 노드 구조 테스트"""
        # 메인넷 가디언 노드가 올바른 구조인지 확인
        assert len(MAINNET_GUARDIAN_NODES) == 3
        assert 'unit-node' in MAINNET_GUARDIAN_NODES
        assert 'hl-node' in MAINNET_GUARDIAN_NODES
        assert 'field-node' in MAINNET_GUARDIAN_NODES
        
        # 모든 공개키가 04로 시작하는지 확인
        for node_id, public_key in MAINNET_GUARDIAN_NODES.items():
            assert public_key.startswith('04')
            assert len(public_key) == 130  # hex string이므로 130자
    
    def test_proposal_dataclass(self):
        """Proposal 데이터클래스 테스트"""
        proposal = Proposal(
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            source_chain="polygon",
            coin_type="ethereum"
        )
        
        assert proposal.destination_address == "0x1234567890123456789012345678901234567890"
        assert proposal.destination_chain == "ethereum"
        assert proposal.asset == "USDC"
        assert proposal.address == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
        assert proposal.source_chain == "polygon"
        assert proposal.coin_type == "ethereum"
    
    def test_verification_result_dataclass(self):
        """VerificationResult 데이터클래스 테스트"""
        result = VerificationResult(
            success=True,
            verified_count=2,
            errors=["test error"],
            verification_details={"node1": True, "node2": False}
        )
        
        assert result.success == True
        assert result.verified_count == 2
        assert result.errors == ["test error"]
        assert result.verification_details == {"node1": True, "node2": False}
    
    def test_signature_length_handling(self):
        """서명 길이 처리 테스트"""
        # 65바이트 서명 (r+s+v)
        signature_65 = base64.b64encode(b'0' * 65).decode()
        # 64바이트 서명 (r+s)
        signature_64 = base64.b64encode(b'0' * 64).decode()
        
        # 두 형식 모두 처리 가능한지 확인
        test_signatures = {
            'field-node': signature_65,
            'hl-node': signature_64,
            'unit-node': signature_64
        }
        
        result = verify_signatures(
            protocol_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            destination_address="0x1234567890123456789012345678901234567890",
            destination_chain="ethereum",
            asset="USDC",
            source_chain="polygon",
            deposit_or_withdraw="deposit",
            signatures=test_signatures
        )
        
        # 더미 서명이므로 False를 반환해야 함
        assert result == False 