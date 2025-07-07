from fastapi import FastAPI
from app.api import price

app = FastAPI()

# 라우터 등록
app.include_router(price.router, prefix="/price")