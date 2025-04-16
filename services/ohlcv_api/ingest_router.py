from fastapi import APIRouter, HTTPException
from typing import List
from utils.schemas import OHLCVModel
from utils.config import load_config
from utils.redis_queue import get_redis_client, save_ohlcv_batch

router = APIRouter()

config = load_config()
redis = get_redis_client(config)
MAX_CANDLES = config.get("max_candles", 500)
INTERVAL = config.get("interval", "1min")

@router.post("/ingest")
async def ingest_ohlcv(data: List[OHLCVModel]):
    try:
        symbol = data[0].symbol.upper() if data else None
        if not symbol:
            raise HTTPException(status_code=400, detail="Missing symbol in OHLCV payload.")

        # Convert list of models to list of dicts
        ohlcv_dicts = [item.dict() for item in data]

        save_ohlcv_batch(redis, symbol, INTERVAL, ohlcv_dicts, MAX_CANDLES)
        return {"message": "✅ OHLCV data stored", "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ Failed to store OHLCV: {str(e)}")
