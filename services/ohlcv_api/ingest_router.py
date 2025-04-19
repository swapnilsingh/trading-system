from fastapi import APIRouter, HTTPException
from typing import List
from utils.schemas import OHLCVModel
from utils.config import load_config
from utils.redis_queue import get_redis_client, save_ohlcv_batch
import logging

logger = logging.getLogger("IngestService")
router = APIRouter()

# Load the config and Redis client
config = load_config()
redis = get_redis_client(config)
MAX_CANDLES = config.get("max_candles", 500)
INTERVAL = config.get("interval", "1min")

@router.post("/ingest")
async def ingest_ohlcv(data: List[OHLCVModel]):
    if not data:
        raise HTTPException(status_code=400, detail="Empty OHLCV payload.")

    try:
        # Ensure symbol is always in uppercase
        symbol = data[0].symbol.upper()

        # Convert the input data to a dictionary for saving
        ohlcv_dicts = [item.dict() for item in data]

        # Save the OHLCV data batch to Redis, handle max candles logic
        save_ohlcv_batch(redis, symbol, INTERVAL, ohlcv_dicts, MAX_CANDLES)

        # Log successful data ingestion
        logger.info(f"Successfully stored {len(data)} OHLCV records for symbol {symbol}.")

        return {"message": "✅ OHLCV data stored", "count": len(data)}

    except Exception as e:
        # Log the exception for internal debugging
        logger.error(f"Failed to store OHLCV data for {symbol}: {str(e)}", exc_info=True)

        # Return an internal server error if something goes wrong
        raise HTTPException(status_code=500, detail=f"Failed to store OHLCV data: {str(e)}")
