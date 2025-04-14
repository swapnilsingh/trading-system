import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import websockets
import json
from datetime import datetime
import logging
from utils.config import load_config
from utils.schemas import TICK_SCHEMA, format_tick_data

# Toggle JSON logging
USE_JSON_LOGS = True

# Setup logger
logger = logging.getLogger("BinanceTickStreamer")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()

if USE_JSON_LOGS:
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
logger.addHandler(handler)
logger.propagate = False

class BinanceTickStreamer:
    def __init__(self, config, on_tick_callback=None):
        self.config = config
        self.symbol = config["symbol"].lower()
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@trade"
        self.on_tick_callback = on_tick_callback

    async def connect_and_stream(self):
        logger.info(f"Connecting to Binance WebSocket for {self.symbol.upper()}...")
        async for websocket in websockets.connect(self.ws_url):
            try:
                async for message in websocket:
                    data = json.loads(message)
                    tick_data = {
                        "symbol": self.symbol.upper(),
                        "price": float(data['p']),
                        "quantity": float(data['q']),
                        "trade_time": datetime.utcfromtimestamp(data['T'] / 1000).isoformat() + "Z"
                    }
                    logger.debug(f"Raw WebSocket message: {data}")
                    formatted = format_tick_data(tick_data)
                    if self.on_tick_callback:
                        await self.on_tick_callback(formatted)
                    else:
                        logger.info(json.dumps(formatted))

            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed. Reconnecting in 3 seconds...")
                await asyncio.sleep(3)
            except Exception as e:
                logger.exception(f"Unexpected error occurred: {e}. Reconnecting in 3 seconds...")
                await asyncio.sleep(3)

# Example callback: Print to console
if __name__ == "__main__":
    async def print_tick(tick):
        logger.info(json.dumps(tick))

    config = load_config()
    streamer = BinanceTickStreamer(config, on_tick_callback=print_tick)
    asyncio.run(streamer.connect_and_stream())
