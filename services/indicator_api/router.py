from fastapi import APIRouter, HTTPException, Body
from utils.schemas import IndicatorCalculationRequest, sanitize_for_json
from core.indicators.registry import registry
from utils.redis_queue import get_redis_client
from utils.data_utils import parse_ohlcv_list
import logging
import pandas as pd

logger = logging.getLogger("IndicatorService")
router = APIRouter()

@router.post("/calculate")
def calculate_indicators(payload: IndicatorCalculationRequest = Body(...)):
    redis_client = get_redis_client()
    if not payload.interval.strip():
        raise HTTPException(status_code=400, detail="Interval cannot be empty")
    results = {}

    if not payload.indicators:
        raise HTTPException(status_code=400, detail="At least one indicator must be provided.")

    for name, details in payload.indicators.items():
        try:
            # Early validation for unsupported indicators
            compute_func = registry.get(name)
            if not compute_func:
                raise HTTPException(status_code=400, detail=f"Indicator '{name}' not supported")

            # Parse Redis OHLCV data
            redis_key = f"ohlcv:{payload.symbol}:{payload.interval}"
            raw_ohlcv_list = redis_client.lrange(redis_key, 0, -1)
            df = parse_ohlcv_list(raw_ohlcv_list)

            # Ensure timestamps are valid integers
            try:
                start = int(details.start_time)
                end = int(details.end_time)
            except ValueError as ve:
                raise HTTPException(status_code=422, detail=f"Invalid start/end time for '{name}': {str(ve)}")

            # Time range filter
            df = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)]
            if df.empty:
                raise HTTPException(status_code=404, detail=f"No OHLCV data found for {name} in range")

            # Compute indicator
            result = compute_func(df, details.params or {})
            if not isinstance(result, dict):
                raise HTTPException(status_code=500, detail=f"{name} did not return a valid result")

            # Check for empty or invalid results
            if all(v is None or (isinstance(v, float) and pd.isna(v)) for v in result.values()):
                logger.warning(f"⚠️ {name} returned only null/NaN values")
                raise HTTPException(status_code=422, detail=f"{name} returned all None or NaN values")

            results[name] = sanitize_for_json(result)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error while computing {name}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error computing {name}: {str(e)}")
        
        if not results:
            raise HTTPException(status_code=400, detail="No valid indicators provided or all failed")

    return results
