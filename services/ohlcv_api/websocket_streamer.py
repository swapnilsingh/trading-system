# websocket_streamer.py
import json
import redis
import websocket
from utils.config import load_config

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# WebSocket URL
config = load_config()
BINANCE_WS_URL = config.get("binance", {}).get("ws_url", "wss://stream.binance.com:9443/ws/btcusdt@trade")

def on_message(ws, message):
    """Callback function for handling incoming WebSocket messages."""
    msg = json.loads(message)
    trade_data = {
        "price": msg["p"],
        "quantity": msg["q"],
        "timestamp": msg["T"]  # Timestamp from Binance
    }
    redis_client.lpush("binance:btc_usdt", json.dumps(trade_data))  # Store in Redis

def start_websocket():
    """Initialize and start the WebSocket connection."""
    ws = websocket.WebSocketApp(BINANCE_WS_URL, on_message=on_message)
    ws.run_forever()

# Start WebSocket in a background thread
if __name__ == "__main__":
    start_websocket()
