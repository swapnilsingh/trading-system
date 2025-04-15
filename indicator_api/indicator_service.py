import json
import pandas as pd
from io import StringIO
from fastapi import FastAPI, HTTPException
from utils.indicator_schema import IndicatorAPIRequest
from utils.schemas import format_indicator_data
from utils.redis_queue import get_redis_client, load_config
from indicator_api.indicators import registry

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("IndicatorService")

app = FastAPI()

@app.post("/indicators/calculate")
async def calculate_indicators(request: IndicatorAPIRequest):
    cfg = load_config()
    redis_client = get_redis_client(cfg)
    results = {}

    for name, details in request.indicators.items():
        redis_key = f"ohlcv:{request.symbol}:{request.interval}"
        raw_ohlcv_list = redis_client.lrange(redis_key, 0, -1)

        if not raw_ohlcv_list:
            raise HTTPException(status_code=404, detail=f"No OHLCV data found for {request.symbol}:{request.interval}")

        try:
            # Parse Redis list into DataFrame
            ohlcv_records = [json.loads(row.decode("utf-8")) for row in raw_ohlcv_list]
            df = pd.DataFrame(ohlcv_records)

            # Convert and index timestamp
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", errors="coerce")
            df = df[df["timestamp"].notnull()]
            df.set_index("timestamp", inplace=True)
            df = df.sort_index()

            # Debug logs
            logger.info(f"[{name}] Index dtype: {df.index.dtype}")
            logger.info(f"[{name}] Index sample: {df.index[:3]}")
            logger.info(f"[{name}] Range: {details.start_time} → {details.end_time}")

            # Time slicing
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
