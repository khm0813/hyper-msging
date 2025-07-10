from fastapi import FastAPI
from app.api import price
from app.api import trading

app = FastAPI()

# 라우터 등록
app.include_router(price.router, prefix="/price")
app.include_router(trading.router, prefix="/trading")