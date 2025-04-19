# services/ohlcv_api/fetch_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import requests
import json
import httpx
from utils.schemas import OHLCVRequest
from utils.config import load_config
from utils.redis_queue import get_redis_client
from utils.redis_queue import (
    fetch_ohlcv_range,
    save_ohlcv_batch
)

router = APIRouter()

config = load_config()
BINANCE_REST_URL = config.get("binance", {}).get("rest_url", "https://api.binance.com/api/v3/klines")
STREAMER_URL = config.get("streamer", {}).get("url", "http://websocket-streamer:8020")
MAX_CANDLES = config.get("max_candles", 500)


@router.post("/fetch")
def fetch_ohlcv(request: OHLCVRequest):
    symbol = request.symbol.upper()
    interval = request.interval

    redis_client = get_redis_client(config)  # Lazy initialization to support mocking in tests

    if request.start_time is not None and request.end_time is not None:
        cached_data = fetch_ohlcv_range(redis_client, symbol, interval, request.start_time, request.end_time)
        if cached_data:
            return {"source": "redis", "data": cached_data}

    # Fallback to Binance REST
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1000
    }
    if request.start_time:
        params["startTime"] = request.start_time
    if request.end_time:
        params["endTime"] = request.end_time

    response = requests.get(BINANCE_REST_URL, params=params)
    if response.status_code != 200:
        # If REST failed, trigger WebSocket Streamer to start
        try:
            stream_payload = {"symbol": symbol, "interval": interval}
            httpx.post(f"{STREAMER_URL}/start", json=stream_payload, timeout=5.0)
        except Exception:
            raise HTTPException(status_code=502, detail="Failed to fetch from Binance and trigger streamer")
        raise HTTPException(status_code=500, detail="❌ Failed to fetch from Binance")

    candles = []
    for row in response.json():
        # Only include data if required fields exist
        try:
            candles.append({
                "timestamp": row[0],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "symbol": symbol,
                "start_time": row[0],
                "end_time": row[0] + 60000  # assume 1-minute candle for fallback
            })
        except (IndexError, ValueError) as e:
            continue

    save_ohlcv_batch(redis_client, symbol, interval, candles, max_candles=MAX_CANDLES)

    return {"source": "binance", "data": candles}
