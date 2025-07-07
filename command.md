# 실행
poetry run uvicorn app.main:app --reload

# 테스트
poetry run pytest --cov=app