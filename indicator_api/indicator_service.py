# indicator_api/indicator_service.py
import json
import pandas as pd
from io import StringIO
from fastapi import FastAPI, HTTPException
from utils.indicator_schema import IndicatorAPIRequest
from utils.schemas import format_indicator_data
from utils.redis_queue import get_redis_client, load_config
from indicator_api.indicators import registry  # updated path for indicators module

app = FastAPI()

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("IndicatorService")

@app.post("/indicators/calculate")
async def calculate_indicators(request: IndicatorAPIRequest):
    cfg = load_config()
    redis_client = get_redis_client(cfg)
    results = {}

    for name, details in request.indicators.items():
        raw_ohlcv = redis_client.get(f"ohlcv:{request.symbol}:{request.interval}")
        if not raw_ohlcv:
            raise HTTPException(status_code=404, detail=f"OHLCV data for {request.symbol}:{request.interval} not found")

        try:
            # Decode Redis string
            raw_ohlcv_str = raw_ohlcv if isinstance(raw_ohlcv, str) else raw_ohlcv.decode("utf-8")

            # Load DataFrame without automatic date parsing
            df = pd.read_json(StringIO(raw_ohlcv_str), convert_dates=False)

            # Ensure timestamp index is in epoch milliseconds
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
                df.set_index("timestamp", inplace=True)
            else:
                df.index = pd.to_datetime(df.index, errors="coerce")

            # Drop rows with invalid timestamps
            df = df[df.index.notnull()]
            df = df.sort_index()

            # Debug logging
            logger.info(f"[{name}] Index dtype: {df.index.dtype}")
            logger.info(f"[{name}] Index sample: {df.index[:3]}")
            logger.info(f"[{name}] Range: {details.start_time} → {details.end_time}")

            # Filter by time window
            start = pd.to_datetime(details.start_time)
            end = pd.to_datetime(details.end_time)
            df = df[(df.index >= start) & (df.index <= end)].copy()

            if df.empty:
                raise HTTPException(status_code=422, detail=f"No OHLCV data in selected range for {name}")

            latest = df.iloc[-1]
            indicator_output = {
                "symbol": request.symbol,
                "timestamp": str(latest.name)
            }

            if name in registry:
                result = registry[name](df, details.params or {})
                indicator_output.update(result)
            else:
                raise HTTPException(status_code=400, detail=f"Indicator '{name}' not supported")

            results[name] = format_indicator_data(indicator_output)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to compute {name}: {e}")

    return results
