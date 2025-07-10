# 통합 트레이딩 허브 Toy Project

HyperEVM, Discord, Twitter, Meteora, Polymarket, Kalshi 등 다양한 온체인·API 기반 거래소/서비스를 FastAPI 마이크로서비스로 통합하는 프로젝트입니다.  
온체인 가격 조회, 알림·소셜 자동화, DeFi 스왑, 예측시장 베팅 등 전체 플로우를 경험할 수 있습니다.

---

## 📚 주요 API 사용법

### 1. 지갑 생성 및 입금주소 생성

- **Endpoint:**  
  `GET /trading/gen_wallet`

- **설명:**  
  새로운 이더리움 지갑을 생성하고, Hyperliquid 거래를 위한 ETH/SOL 입금주소를 생성합니다. 생성된 입금주소는 Hyperunit API를 통해 검증된 서명과 함께 반환됩니다.

- **Response 예시:**
  ```json
  {
    "wallet": {
      "address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
      "private_key": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    },
    "deposit_address": {
      "ETH": {
        "address": "0x3F344...",
        "signatures": {
          "field-node": "A/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
          "hl-node": "roOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
          "unit-node": "JO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
        },
        "status": "OK"
      },
      "SOL": {
        "address": "0x5A2b3...",
        "signatures": {
          "field-node": "B/o6b5CTyjyV4MVDtt15+/c4078OHCf8vatkHs8wQm3dX6Gs784br5uUoCnATXYG94RwBiHpaEOLlJiDyMzH2A==",
          "hl-node": "soOKVA5o4O+MsKfqWB1yHnII6jyysIdEIuSSEHFlV2QYTKHvPC6rQPqhsZ1m1kCm3Zq4lUKykRZzpnU0bx1dsg==",
          "unit-node": "KO44LIE5Q4DpNzw9nsKmgTKqpm7M8wsMTCqgSUJ3LpTWvd0wQDVh+H7VTJb87Zf0gZiu/JkKCK1Tf4+IabzZgw=="
        },
        "status": "OK"
      }
    }
  }
  ```

- **오류 응답 예시:**
  - ETH 입금주소 생성 실패:
    ```json
    { "detail": "ETH 입금 주소 생성 실패" }
    ```
  - SOL 입금주소 생성 실패:
    ```json
    { "detail": "SOL 입금 주소 생성 실패" }
    ```
  - Upstream API 오류:
    ```json
    { "detail": "Upstream RPC error" }
    ```

---

### 2. 지갑 잔고 조회

- **Endpoint:**  
  `GET /trading/wallet_balance`

- **설명:**  
  Hyperliquid 지갑의 현재 잔고를 조회합니다. 계정 가치, 출금 가능 금액, 마진 사용량, 자산 포지션 등의 상세 정보를 반환합니다.

- **Query Parameter:**  
  - `address` (str): Hyperliquid 지갑 주소 (0x...)

- **Response 예시 (잔고가 있는 경우):**
  ```json
  {
    "address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
    "balance": {
      "account_value": "1000.50",
      "withdrawable": "800.40",
      "total_margin_used": "200.10",
      "total_notional_position": "500.25",
      "total_raw_usd": "1000.50",
      "asset_positions": [
        {
          "coin": "USDC",
          "position": "1000.50",
          "notionalUsd": "1000.50"
        }
      ],
      "cross_margin_summary": {
        "accountValue": "1000.50",
        "totalNtlPos": "500.25",
        "totalRawUsd": "1000.50",
        "totalMarginUsed": "200.10"
      },
      "timestamp": 1752146173198
    }
  }
  ```

- **Response 예시 (잔고가 없는 경우):**
  ```json
  {
    "address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
    "balance": {
      "account_value": "0.0",
      "withdrawable": "0.0",
      "total_margin_used": "0.0",
      "asset_positions": [],
      "message": "잔고 없음 또는 신규 지갑"
    }
  }
  ```

- **오류 응답 예시:**
  - 주소 파라미터 누락:
    ```json
    { "detail": "Field required" }
    ```
  - API 연결 실패:
    ```json
    { "detail": "Hyperliquid API 연결 실패" }
    ```
  - 요청 시간 초과:
    ```json
    { "detail": "Hyperliquid API 요청 시간 초과" }
    ```

---

### 3. 실시간 가격 조회

- **Endpoint:**  
  `GET /price/{market_id}`

- **설명:**  
  Hyperliquid(예시) 마켓의 실시간 가격을 조회합니다.

- **Path Parameter:**  
  - `market_id` (int): 마켓 인덱스 (0부터 시작)

- **Response 예시:**
  ```json
  {
    "market_id": 1,
    "symbol": "BTC",
    "price": 69123.5
  }
  ```

- **오류 응답 예시:**
  - market_id가 음수일 때:
    ```json
    { "detail": "market_id must be non-negative" }
    ```
  - 존재하지 않는 market_id:
    ```json
    { "detail": "Invalid market_id: 999" }
    ```

- **Swagger/OpenAPI 문서:**  
  [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 4. 심볼별 펀딩비/이자율 조회

- **Endpoint:**  
  `GET /price/funding/{symbol}`

- **설명:**  
  Hyperliquid 마켓의 심볼별 펀딩비(이자율) 정보를 조회합니다.

- **Path Parameter:**  
  - `symbol` (str): 코인 심볼 (예: BTC, ETH)

- **Response 예시:**
  ```json
  {
    "symbol": "BTC",
    "funding": 0.0000125
  }
  ```

- **오류 응답 예시:**
  - 잘못된 심볼:
    ```json
    { "detail": "Invalid symbol" }
    ```
  - 존재하지 않는 심볼:
    ```json
    { "detail": "Symbol not found: NOTREAL" }
    ```
  - Upstream API 오류:
    ```json
    { "detail": "Upstream RPC error" }
    ```

---

### 5. 심볼별 트레이딩 주요 지표(컨텍스트) 조회

- **Endpoint:**  
  `GET /price/asset_ctx/{symbol}`

- **설명:**  
  Hyperliquid 마켓의 심볼별 트레이딩 주요 지표(컨텍스트) 정보를 조회합니다. (펀딩비, 미결제약정, 마크가격, 오라클가격, 프리미엄, 24시간 거래량 등)

- **Path Parameter:**  
  - `symbol` (str): 코인 심볼 (예: BTC, ETH)

- **Response 예시:**
  ```json
  {
    "symbol": "BTC",
    "funding": 0.0000125,
    "openInterest": 34345.24704,
    "markPx": 108889.0,
    "midPx": 108889.5,
    "oraclePx": 108859.0,
    "premium": 0.0002755858,
    "prevDayPx": 108232.0,
    "dayNtlVlm": 2138608387.4016401768,
    "impactPxs": [108889.0, 108890.0],
    "dayBaseVlm": 19671.09977
  }
  ```

- **오류 응답 예시:**
  - 잘못된 심볼:
    ```json
    { "detail": "Invalid symbol" }
    ```
  - 존재하지 않는 심볼:
    ```json
    { "detail": "Symbol not found: NOTREAL" }
    ```
  - Upstream API 오류:
    ```json
    { "detail": "Upstream RPC error" }
    ```

---



---

## 🛠️ 사용한 주요 외부 라이브러리

| 역할            | 라이브러리/도구         |
|----------------|------------------------|
| 웹 프레임워크   | fastapi                |
| ASGI 서버      | uvicorn[standard]      |
| HTTP client    | httpx                  |
| 설정 관리      | pydantic, pydantic-settings |
| Pub/Sub        | redis                  |
| 이더리움 연동  | web3                   |
| 테스트         | pytest, respx, pytest-mock |
| 코드 스타일    | black, flake8, mypy    |

> 전체 의존성은 `pyproject.toml` 참고

---

## ⚙️ 설치 및 실행

1. **코드 클론**
    ```sh
    git clone https://github.com/<owner>/<repo>.git
    cd <repo>
    ```

2. **환경파일 복사 및 설정**
    ```sh
    cp .env.example .env
    # .env 파일에 HYPERLIQUID_API_URL 등 값 입력
    ```

3. **개발용 Docker Compose 실행**
    ```sh
    docker-compose -f docker-compose.dev.yml up --build
    ```

4. **FastAPI 서버 접속**
    - [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

---

## ✔️ 테스트

```sh
pytest --cov=app
```

---

## 📁 폴더 구조

```
├── app/
│   ├── api/                # FastAPI 엔드포인트
│   ├── core/               # 비즈니스 로직 (Hyperevm 등)
│   ├── config.py           # 환경설정
│   └── main.py             # FastAPI 앱 진입점
├── tests/                  # pytest 테스트 코드
├── docker-compose.dev.yml  # 개발용 Docker Compose
├── docker-compose.prod.yml # 운영용 Docker Compose
├── .env.example            # 환경변수 템플릿
├── pyproject.toml          # 의존성 및 스크립트
└── README.md               # 프로젝트 설명
```

---

## 🤝 기여

- Issue/PR 환영!  
- 코드 스타일: black, flake8, mypy 권장  
- pre-commit hook 사용 추천

---

더 많은 API와 기능은 앞으로 추가될 예정입니다.  
문의/기여는 언제든 환영합니다!

---

## 개발 예정 기능 (Hypeliquid API 기반)

1. **심볼별 호가(오더북) 조회 API**
   - 특정 심볼의 실시간 오더북(매수/매도 호가, 수량) 정보를 반환하는 엔드포인트 개발
   - 프론트엔드 차트, 트레이딩 봇 등에서 실시간 유동성 파악에 활용
   - Hypeliquid의 오더북 REST/WebSocket API 연동

2. **최근 체결 내역(트레이드 히스토리) 조회 API**
   - 심볼별로 최근 거래(체결) 내역을 조회하는 엔드포인트 제공
   - 거래량, 가격 변동성 분석, 사용자 거래 내역 시각화 등에 활용
   - 페이징, 시간 범위 필터 등 지원 예정

3. **심볼별 캔들(OHLCV) 데이터 조회 API**
   - 분/시/일 단위의 캔들스틱(시가, 고가, 저가, 종가, 거래량) 데이터 제공
   - 차트, 백테스팅, 전략 개발 등에 활용
   - 기간, 심볼, 캔들 타입(분/시/일) 파라미터 지원

4. **심볼별 미체결 주문(오픈 오더) 조회 API**
   - 특정 계정 또는 심볼의 미체결 주문 목록 반환
   - 포지션 관리, 자동화 트레이딩에 활용
   - 인증/인가(계정별 접근 제한) 기능 연동 예정

5. **심볼별 포지션 정보 조회 API**
   - 특정 계정의 심볼별 포지션(진입가, 수량, 미실현 PnL 등) 정보 제공
   - 리스크 관리, 대시보드 등에 활용
   - 계정 인증, 실시간 데이터 동기화 고려

6. **시장 전체 심볼/마켓 리스트 및 메타데이터 조회 API**
   - 거래 가능한 모든 심볼, 마켓 정보(상태, 최소 주문 단위 등) 반환
   - 심볼 선택 UI, 자동화 스크립트 등에 활용
   - Hypeliquid의 심볼/마켓 메타데이터 API 연동

7. **심볼별 펀딩비/이자율 정보 조회 API**
   - 파생상품의 펀딩비, 이자율 등 파라미터 제공
   - 장기 포지션 전략, 수익률 분석 등에 활용
   - 펀딩비 이력, 예측값 등 추가 제공 검토

8. **심볼별 가격 알림/트리거 등록 API**
   - 특정 가격 도달 시 알림(웹훅, 푸시 등) 등록 및 관리
   - 자동매매, 사용자 알림 서비스 등에 활용
   - 비동기 작업/이벤트 처리 구조 설계 예정

9. **시장 상태(정상/점검/이상 등) 조회 API**
   - 심볼 또는 전체 마켓의 운영 상태 반환
   - 서비스 모니터링, 장애 대응 등에 활용
   - 상태 변화 감지 및 알림 기능 연동 검토

10. **심볼별 거래량/유동성 통계 API**
    - 최근 24시간 거래량, 유동성 등 통계 데이터 제공
    - 마켓 분석, 전략 선정 등에 활용
    - 기간별, 심볼별 통계 파라미터 지원