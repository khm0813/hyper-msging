통합 트레이딩 허브 Toy Project

HyperEVM, Discord, Twitter, Meteora DLMM, Polymarket & Kalshi 모듈을 FastAPI 마이크로서비스로 통합하여,
온체인 가격 조회부터 알림·소셜 자동화, DeFi 스왑, 예측시장 베팅까지의 전체 플로우를 경험할 수 있는 프로젝트입니다.

⸻

📘 프로젝트 개요
	•	이름: 통합 트레이딩 허브 Toy Project
	•	목표: 다양한 온체인·API 기반 거래소 솔루션을 단일 백엔드로 연결
	•	주요 기능:
	1.	HyperEVM 가격 조회: EVM DEX 트레이딩 체인에서 실시간 가격 수집
	2.	이벤트 버스: Redis Pub/Sub으로 모듈 간 이벤트 전달
	3.	Discord 알림: 주요 가격 변경 시 지정 채널에 메시지 전송
	4.	Twitter 자동 포스팅: 동일 이벤트를 트윗으로 자동 발행
	5.	Meteora DLMM 스왑: DLMM SDK 연동으로 샘플 스왑 실행
	6.	Polymarket 베팅: L1/L2 인증을 거쳐 예측시장 주문 제출
	7.	Kalshi 베팅: RSA 서명 기반 API 호출로 미국 규제 예측시장 주문

⸻

📐 아키텍처

+--------------+      +----------------+      +--------------+
| FastAPI      | <--> | Redis Pub/Sub  | <--> | Discord Bot  |
| API Gateway  |      |  (price_event) |      +--------------+
|              |      +----------------+      +--------------+
|  /price/...  |                            | Twitter Bot  |
|  /swap/...   |                            +--------------+
|  /bet/...    |                            +--------------+
+--------------+                            | Meteora Svc  |
                                             +--------------+
                                             +--------------+
                                             | Polymarket   |
                                             +--------------+
                                             +--------------+
                                             | Kalshi Svc   |
                                             +--------------+

	•	MSA 기반: 모든 모듈이 독립적이며 Pub/Sub으로 느슨하게 결합
	•	Dev / Prod 환경 분리: 별도 설정 클래스와 Compose 파일

⸻

🛠 기술 스택

역할	라이브러리 / 도구
웹 프레임워크	FastAPI (Python 3.11)
ASGI 서버	Uvicorn
DB/ORM	SQLModel / SQLite (Toy 용)
설정 관리	Pydantic BaseSettings
HTTP client	httpx
Pub/Sub	redis-py
이더리움	etherspy
Discord Bot	discord.py
Twitter Bot	tweepy or httpx
Meteora DLMM	meteora-dlmm-sdk (wrap)
Polymarket	polymarket-python
Kalshi	requests + cryptography
테스트	pytest, respx, pytest-mock, coverage
린트·형식검사	black, flake8, mypy
CI/CD	GitHub Actions


⸻

📁 폴더 구조

├── app/
│   ├── api/                # FastAPI 엔드포인트
│   ├── core/               # 비즈니스 로직 (Hyperevm, Redis 등)
│   ├── services/           # 외부 연동 모듈 (Discord, Twitter 등)
│   ├── config.py           # DevSettings / ProdSettings
│   └── main.py             # FastAPI 앱 진입점
├── tests/                  # pytest 테스트 코드
│   └── test_placeholder.py 
├── docker/
│   ├── docker-compose.dev.yml
│   └── docker-compose.prod.yml
├── .env.example            # 환경변수 템플릿
├── .cursorrules            # Cursor AI 규칙
├── pyproject.toml          # 의존성 및 스크립트
└── README.md               # 프로젝트 설명 (이 파일)


⸻

⚙️ 설치 및 실행
	1.	코드 클론

git clone https://github.com/<owner>/<repo>.git
cd <repo>


	2.	환경파일 복사 및 설정

cp .env.example .env
# .env 에 GITHUB_TOKEN, HYPEREVM_RPC_URL, DISCORD_TOKEN 등 값 입력


	3.	개발용 Docker Compose 실행

docker-compose -f docker/docker-compose.dev.yml up --build


	4.	FastAPI 서버 접속
	•	http://localhost:8000/docs

⸻

✔️ 테스트

# 로컬 실행
pytest --cov=app

# CI 단계: coverage ≥ 80%


⸻

📜 문서화
	•	OpenAPI: /docs, /redoc
	•	추가 문서: docs/ 에 Sphinx 또는 MkDocs 프로젝트 구성 추천

⸻

🤝 기여 및 커뮤니케이션
	•	Issue: 기능 제안, 버그 리포트는 GitHub Issue로
	•	PR: develop 브랜치로 머지 리퀘스트 생성, Closes #ISSUE_ID 사용
	•	코드 스타일: pre-commit Hook 설정 권장 (black, flake8)

⸻

이제 이 README를 참고하여 전체 플로우를 탐색하고 개발을 시작하세요!