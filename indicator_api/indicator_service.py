# indicator_api/indicator_service.py
import json
import pandas as pd
from io import StringIO
from fastapi import FastAPI, HTTPException
from utils.indicator_schema import IndicatorAPIRequest
from utils.schemas import format_indicator_data
from utils.redis_queue import get_redis_client, load_config
from indicators import registry

app = FastAPI()

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
            df = pd.read_json(StringIO(raw_ohlcv.decode("utf-8")))
            df = df[(df.index >= details.start_time) & (df.index <= details.end_time)]
            df = df.copy()

            latest = df.iloc[-1]
            indicator_output = {"symbol": request.symbol, "timestamp": str(latest.name)}

            if name in registry:
                result = registry[name](df, details.params or {})
                indicator_output.update(result)
            else:
                raise HTTPException(status_code=400, detail=f"Indicator '{name}' not supported")

            results[name] = format_indicator_data(indicator_output)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to compute {name}: {e}")

    return results
