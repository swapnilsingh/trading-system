import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from fastapi import FastAPI
from services.indicator_api.router import router

app = FastAPI(title="Indicator API Service")
app.include_router(router, prefix="/indicators")
