from pydantic import BaseModel
from typing import List
from fastapi import APIRouter, HTTPException

try:
    import cupy as cp
except ImportError:
    import numpy as cp

router = APIRouter()

class Tick(BaseModel):
    price: float
    quantity: float
    timestamp: int

class TickFeatureRequest(BaseModel):
    symbol: str
    ticks: List[Tick]

class TickFeatureResponse(BaseModel):
    vwap: float
    price_delta: float
    total_volume: float

@router.post("/tick_features", response_model=TickFeatureResponse)
def compute_tick_features(request: TickFeatureRequest):
    if not request.ticks or len(request.ticks) < 2:
        raise HTTPException(status_code=400, detail="At least 2 ticks are required")

    prices = cp.array([tick.price for tick in request.ticks])
    volumes = cp.array([tick.quantity for tick in request.ticks])

    vwap = float(cp.sum(prices * volumes) / cp.sum(volumes))
    price_delta = float(prices[-1] - prices[0])
    total_volume = float(cp.sum(volumes))

    return TickFeatureResponse(
        vwap=round(vwap, 4),
        price_delta=round(price_delta, 4),
        total_volume=round(total_volume, 4),
    )
