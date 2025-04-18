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
from utils.schemas import TICK_SCHEMA, format_tick_data
from utils.redis_queue import get_redis_client, push_to_queue

BUFFER = defaultdict(list)

class BinanceTickStreamer:
    def __init__(self, config, on_tick_callback=None):
        self.config = config
        self.symbol = config["symbol"].lower()
        self.interval = config.get("interval", "1min")
        self.use_json_logs = config.get("use_json_logs", False)
        self.max_candles = config.get("max_candles", 500)

        ws_base = config.get("websocket", {}).get("base_url", "wss://stream.binance.com:9443")
        stream_type = config.get("websocket", {}).get("stream_type", "trade")
        self.ws_url = f"{ws_base}/ws/{self.symbol}@{stream_type}"

        self.on_tick_callback = on_tick_callback
        self.redis = get_redis_client(config)

        self.logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger("BinanceTickStreamer")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()

        if self.use_json_logs:
            class JSONFormatter(logging.Formatter):
                def format(self, record):
                    log_record = {
                        "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
                        "level": record.levelname,
                        "module": record.name,
                        "message": record.getMessage(),
                    }
                    return json.dumps(log_record)
            formatter = JSONFormatter()
        else:
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

if __name__ == "__main__":
    config = load_config()
    streamer = BinanceTickStreamer(config)
    asyncio.run(streamer.connect_and_stream())
