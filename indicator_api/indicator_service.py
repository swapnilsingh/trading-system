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
            # Decode Redis response to string
            raw_ohlcv_str = raw_ohlcv if isinstance(raw_ohlcv, str) else raw_ohlcv.decode("utf-8")

            # Read JSON safely without automatic date inference
            df = pd.read_json(StringIO(raw_ohlcv_str), convert_dates=False)

            # Ensure timestamp column or index is datetime and used as index
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                df.set_index("timestamp", inplace=True)
            else:
                df.index = pd.to_datetime(df.index, errors="coerce")

            # Drop NaT values caused by parsing errors
            df = df[df.index.notnull()]

            # Convert provided start/end window to datetime
            start = pd.to_datetime(details.start_time)
            end = pd.to_datetime(details.end_time)

            # Filter by time range
            df = df[(df.index >= start) & (df.index <= end)].copy()

            if df.empty:
                raise HTTPException(status_code=422, detail=f"No OHLCV data in selected range for {name}")

            # Prepare base response
            latest = df.iloc[-1]
            indicator_output = {
                "symbol": request.symbol,
                "timestamp": str(latest.name)
            }

            # Compute indicator using registry
            if name in registry:
                result = registry[name](df, details.params or {})
                indicator_output.update(result)
            else:
                raise HTTPException(status_code=400, detail=f"Indicator '{name}' not supported")

            results[name] = format_indicator_data(indicator_output)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to compute {name}: {e}")

    return results
