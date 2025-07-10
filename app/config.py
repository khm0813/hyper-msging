from pydantic import BaseModel
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Hyperliquid API 설정
    HYPEREVM_RPC_URL: str = "https://rpc.hyperliquid.xyz/evm"
    HYPERLIQUID_API_URL: str = "https://api.hyperliquid.xyz"
    HYPERLIQUID_WS_URL: str = "wss://api.hyperliquid.xyz/ws"
    
    # API 인증 (필요시)
    HYPERLIQUID_API_ADDRESS: str = ""   
    HYPERLIQUID_API_PRIVATE: str = ""
    
    # Redis 설정 (실시간 데이터 캐싱용)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 0
    
    # 기타 서비스 토큰들
    DISCORD_TOKEN: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    
    # 애플리케이션 설정
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 전역으로 import 가능한 settings 인스턴스
settings = Settings()