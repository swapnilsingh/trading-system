from fastapi import FastAPI
from endpoints.tick_features import router as tick_router

app = FastAPI(title="GPU Feature Service")

app.include_router(tick_router)
