# 통합 트레이딩 허브 Toy Project

HyperEVM, Discord, Twitter, Meteora, Polymarket, Kalshi 등 다양한 온체인·API 기반 거래소/서비스를 FastAPI 마이크로서비스로 통합하는 프로젝트입니다.  
온체인 가격 조회, 알림·소셜 자동화, DeFi 스왑, 예측시장 베팅 등 전체 플로우를 경험할 수 있습니다.

---

## 📚 주요 API 사용법

### 1. 실시간 가격 조회

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