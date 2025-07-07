# Windows, macOS, Linux 공통
curl -sSL https://install.python-poetry.org | python3 -

(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# 의존성 설치
poetry install

# 실행
poetry run uvicorn app.main:app --reload


# 테스트
poetry run pytest


#