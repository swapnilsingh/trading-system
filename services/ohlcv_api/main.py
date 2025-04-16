from fastapi import FastAPI
from services.ohlcv_api.fetch_router import router as fetch_router
from services.ohlcv_api.ingest_router import router as ingest_router

app = FastAPI()
app.include_router(fetch_router, prefix="/ohlcv")
app.include_router(ingest_router, prefix="/ohlcv")
