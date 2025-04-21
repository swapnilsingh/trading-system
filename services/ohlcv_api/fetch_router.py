# fetch_router.py

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import fetch_binance_data, process_binance_data
from utils.redis_queue import get_redis_client, fetch_ohlcv_range, save_ohlcv_batch
from fastapi import APIRouter, HTTPException
from utils.schemas import OHLCVRequest
import logging

logger = logging.getLogger("ohlcv-api")
router = APIRouter()

@router.post("/fetch")
def fetch_ohlcv(request: OHLCVRequest):
    symbol = request.symbol.upper()
    interval = request.interval
    redis_client = get_redis_client()

    # Check Redis first
    cached_data = fetch_ohlcv_range(redis_client, symbol, interval, request.start_time, request.end_time)
    if cached_data:
        logger.info(f"✅ Returning {len(cached_data)} candles from Redis for {symbol} [{interval}]")
        return {"source": "redis", "data": cached_data}

    # If not in Redis, fetch from Binance REST
    try:
        raw_data = fetch_binance_data(symbol, interval, request.start_time, request.end_time)
        parsed_data = process_binance_data(raw_data, symbol)
        save_ohlcv_batch(redis_client, symbol, interval, parsed_data)
        return {"source": "binance", "data": parsed_data}
    except ValueError as ve:
        logger.error(f"❌ Validation error: {str(ve)}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"🔥 Exception while fetching OHLCV for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch OHLCV from Binance")

