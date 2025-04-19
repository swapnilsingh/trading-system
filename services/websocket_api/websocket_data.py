import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import websockets
import json
from datetime import datetime
import logging
import pandas as pd
from collections import defaultdict
from utils.config import load_config
from utils.schemas import TICK_SCHEMA, format_tick_data, OHLCVRequest
from utils.redis_queue import get_redis_client

BUFFER = defaultdict(list)

class BinanceTickStreamer:
    def __init__(self, symbol, interval="1min", on_tick_callback=None):
        self.symbol = symbol.lower()
        self.interval = interval
        self.use_json_logs = False
        self.max_candles = 500

        ws_base = "wss://stream.binance.com:9443"
        stream_type = "trade"
        self.ws_url = f"{ws_base}/ws/{self.symbol}@{stream_type}"

        self.on_tick_callback = on_tick_callback
        self.redis = get_redis_client()

        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger(f"BinanceTickStreamer:{self.symbol}@{self.interval}")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.propagate = False
        return logger

    def aggregate_and_push(self, minute_key):
        df = pd.DataFrame(BUFFER[minute_key])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        ohlcv = df["price"].resample("1min").ohlc()
        ohlcv["volume"] = df["quantity"].resample("1min").sum()
        ohlcv.reset_index(inplace=True)

        ohlcv["timestamp"] = ohlcv["timestamp"].astype("int64") // 1_000_000
        ohlcv = ohlcv[["timestamp", "open", "high", "low", "close", "volume"]]

        redis_key = f"ohlcv:{self.symbol.upper()}:{self.interval}"
        for row in ohlcv.to_dict(orient="records"):
            self.redis.rpush(redis_key, json.dumps(row))

        self.redis.ltrim(redis_key, 0, self.max_candles - 1)
        self.logger.debug(f"✅ Appended OHLCV to Redis list: {redis_key}")

    async def connect_and_stream(self):
        self.logger.info(f"✅ Connected to Binance WebSocket for {self.symbol.upper()}")
        async for websocket in websockets.connect(self.ws_url):
            try:
                async for message in websocket:
                    data = json.loads(message)
                    tick_data = {
                        "symbol": self.symbol.upper(),
                        "price": float(data['p']),
                        "quantity": float(data['q']),
                        "timestamp": data['T']
                    }
                    minute_ts = data['T'] // 60000 * 60000
                    BUFFER[minute_ts].append(tick_data)

                    if len(BUFFER) > 1:
                        oldest = sorted(BUFFER.keys())[0]
                        self.aggregate_and_push(oldest)
                        del BUFFER[oldest]

            except websockets.ConnectionClosed:
                self.logger.warning("WebSocket connection closed. Reconnecting in 3 seconds...")
                await asyncio.sleep(3)
            except Exception as e:
                self.logger.exception(f"Unexpected error occurred: {e}. Reconnecting in 3 seconds...")
                await asyncio.sleep(3)

STREAMS = {}
STREAM_CONFIGS = {}

async def start_stream(key):
    if key in STREAMS:
        return
    symbol, interval = key
    streamer = BinanceTickStreamer(symbol, interval)
    task = asyncio.create_task(streamer.connect_and_stream())
    STREAMS[key] = task
    STREAM_CONFIGS[key] = {"symbol": symbol, "interval": interval}

async def stop_stream(key):
    task = STREAMS.get(key)
    if not task:
        return False
    task.cancel()
    del STREAMS[key]
    del STREAM_CONFIGS[key]
    return True

async def update_stream(old_key, new_key):
    success = await stop_stream(old_key)
    if not success:
        return False
    symbol, interval = new_key
    await start_stream((symbol, interval))
    return True


def get_active_streams():
    return [f"{k[0]}@{k[1]}" for k in STREAMS.keys()]
