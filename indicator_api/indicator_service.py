# indicator_api/indicator_service.py
import json
import pandas as pd
from fastapi import FastAPI, HTTPException
from utils.indicator_schema import IndicatorAPIRequest
from utils.schemas import format_indicator_data
from utils.redis_queue import get_redis_client, load_config
import ta

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
            df = pd.read_json(raw_ohlcv)
            df = df[(df.index >= details.start_time) & (df.index <= details.end_time)]
            df = df.copy()

            latest = df.iloc[-1]
            indicator_output = {"symbol": request.symbol, "timestamp": str(latest.name)}

            if name == "rsi":
                window = details.params.get("window", 14)
                indicator_output["rsi"] = ta.momentum.RSIIndicator(close=df['close'], window=window).rsi().iloc[-1]

            elif name == "macd":
                macd_params = details.params or {}
                macd = ta.trend.MACD(
                    close=df['close'],
                    window_slow=macd_params.get("slow", 26),
                    window_fast=macd_params.get("fast", 12),
                    window_sign=macd_params.get("signal", 9)
                )
                indicator_output["macd"] = macd.macd().iloc[-1]
                indicator_output["macd_signal"] = macd.macd_signal().iloc[-1]

            elif name == "bollinger":
                bb_params = details.params or {}
                bb = ta.volatility.BollingerBands(
                    close=df['close'],
                    window=bb_params.get("window", 20),
                    window_dev=bb_params.get("std", 2.0)
                )
                indicator_output["bollinger_upper"] = bb.bollinger_hband().iloc[-1]
                indicator_output["bollinger_lower"] = bb.bollinger_lband().iloc[-1]
                indicator_output["bollinger_middle"] = bb.bollinger_mavg().iloc[-1]

            elif name == "atr":
                atr_params = details.params or {}
                window = atr_params.get("window", 14)
                atr = ta.volatility.AverageTrueRange(
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    window=window
                )
                indicator_output["atr"] = atr.average_true_range().iloc[-1]

            elif name.startswith("sma"):
                period = int(name.replace("sma", ""))
                indicator_output[name] = df["close"].rolling(window=period).mean().iloc[-1]

            results[name] = format_indicator_data(indicator_output)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to compute {name}: {e}")

    return results