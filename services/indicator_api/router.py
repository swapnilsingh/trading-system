from fastapi import APIRouter, HTTPException, Body
from utils.schemas import IndicatorCalculationRequest, sanitize_for_json
from core.indicators.registry import registry
from utils.redis_queue import get_redis_client
from utils.data_utils import parse_ohlcv_list
import logging
import pandas as pd
import httpx
import json

logger = logging.getLogger("IndicatorService")
router = APIRouter()

# Validate the incoming request payload
def validate_payload(payload: IndicatorCalculationRequest):
    if not payload:
        raise HTTPException(status_code=422, detail="Request body cannot be empty")
    if not payload.symbol:
        raise HTTPException(status_code=422, detail="Symbol is required")
    if not payload.interval.strip():
        raise HTTPException(status_code=400, detail="Interval cannot be empty")
    if not payload.indicators:
        raise HTTPException(status_code=400, detail="At least one indicator must be provided.")

# Fetch OHLCV data from Redis and filter it by time range
def get_indicator_data(redis_client, symbol, interval, start_time, end_time):
    redis_key = f"ohlcv:{symbol}:{interval}"
    raw_ohlcv_list = redis_client.lrange(redis_key, 0, -1)
    if not raw_ohlcv_list:
        return pd.DataFrame()  # Return an empty DataFrame if no data is found

    df = parse_ohlcv_list(raw_ohlcv_list)

    # If no data is returned from parse_ohlcv_list, return empty DataFrame
    if df.empty:
        logger.warning(f"No OHLCV data for {symbol} from Redis.")
        return df

    # Check if the timestamp column exists
    if 'timestamp' not in df.columns:
        logger.error(f"❌ 'timestamp' column is missing from the data for {symbol}.")
        return pd.DataFrame()

    df = df[(df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)]
    return df


# Fallback to Binance for missing data from Redis
def fallback_to_binance(fallback_payload):
    try:
        response = httpx.post("http://ohlcv-api:8010/ohlcv/fetch", json=fallback_payload, timeout=10.0)
        response.raise_for_status()
        if not response.json():  # If the response is empty or invalid
            raise HTTPException(status_code=404, detail="No data returned from Binance API")
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"HTTP request failed for fallback: {e}")
        raise HTTPException(status_code=502, detail=f"OHLCV API unreachable: {str(e)}")
    except Exception as e:
        logger.error("Fallback failed", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fallback error: {str(e)}")

# Apply the indicator function and sanitize the result
def process_indicator(compute_func, df, params):
    result = compute_func(df, params)
    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail=f"Indicator did not return a valid result")

    if all(v is None or (isinstance(v, float) and pd.isna(v)) for v in result.values()):
        logger.warning(f"Indicator returned only null/NaN values")
        raise HTTPException(status_code=422, detail="Indicator returned all None or NaN values")

    return sanitize_for_json(result)

# services/indicator_api/router.py

@router.post("/calculate")
def calculate_indicators(payload: IndicatorCalculationRequest = Body(...)):
    redis_client = get_redis_client()
    validate_payload(payload)
    results = {}

    for name, details in payload.indicators.items():
        try:
            meta = registry.get(name)
            if not meta or "func" not in meta:
                raise HTTPException(status_code=404, detail=f"Indicator '{name}' not found")
            compute_func = meta["func"]

            try:
                start_time = int(details.start_time)
                end_time = int(details.end_time)
            except ValueError as ve:
                raise HTTPException(status_code=422, detail=f"Invalid start/end time for '{name}': {str(ve)}")

            df = get_indicator_data(redis_client, payload.symbol, payload.interval, start_time, end_time)

            if df.empty:
                logger.warning(f"⚠️ No data in Redis for {payload.symbol}, {name}. Triggering fallback.")
                fallback_payload = {
                    "symbol": payload.symbol,
                    "interval": payload.interval,
                    "start_time": start_time,
                    "end_time": end_time
                }
                binance_data = fallback_to_binance(fallback_payload)
                data_list = binance_data.get('data', [])

                # Check if fallback data is empty
                if not data_list:
                    logger.error(f"❌ Fallback data is empty for {name}")
                    raise HTTPException(status_code=404, detail=f"No OHLCV data after fallback for '{name}'")

                df = parse_ohlcv_list(data_list)

                # Validate parsed DataFrame structure
                if 'timestamp' not in df.columns:
                    logger.error(f"❌ Fallback data missing 'timestamp' column for {name}")
                    raise HTTPException(status_code=500, detail="Invalid OHLCV data format from fallback")

                df = df[(df["timestamp"] >= start_time) & (df["timestamp"] <= end_time)]

                if df.empty:
                    logger.error(f"❌ Fallback data out of time range for {name}")
                    raise HTTPException(status_code=404, detail=f"No data in range after fallback for '{name}'")

            result = process_indicator(compute_func, df, details.params or {})
            results[name] = result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error computing {name}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error computing {name}: {str(e)}")

    return results if results else HTTPException(422, "No indicators computed")
    
@router.get("/catalog")
def get_indicator_catalog():
    try:
        catalog = {
            name: {
                "category": meta.get("category"),
                "description": meta.get("description"),
                "default_params": meta.get("params", {})
            }
            for name, meta in registry.items()
        }
        return {"indicators": catalog}
    except Exception as e:
        logger.error("Failed to fetch indicator catalog", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")