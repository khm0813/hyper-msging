# Windows, macOS, Linux 공통
curl -sSL https://install.python-poetry.org | python3 -

(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Conda
conda install python=3.11.0
conda update --all
conda activate py3_11
conda deactivate

# 의존성 설치
poetry install

# 실행
poetry run uvicorn app.main:app --reload


# 테스트
poetry run pytest
poetry run pytest -s -v
poetry run pytest -s -v tests/test_trading.py::test_gen_wallet_success


#