import requests
from utils.config import load_config

config = load_config()
BINANCE_REST_URL = config.get("binance", {}).get("rest_url", "https://api.binance.com/api/v3/klines")

BINANCE_INTERVAL_MAP = {
    "1min": "1m",
    "3min": "3m",
    "5min": "5m",
    "15min": "15m",
    "30min": "30m",
    "1hour": "1h",
    "1h": "1h",
    "4hour": "4h",
    "1day": "1d",
    "1d": "1d"
}

def fetch_binance_data(symbol, interval, start_time, end_time):
    if start_time is None or end_time is None:
        raise ValueError("start_time and end_time are required")

    normalized_interval = BINANCE_INTERVAL_MAP.get(interval, interval)
    url = BINANCE_REST_URL
    params = {
        "symbol": symbol,
        "interval": normalized_interval,
        "startTime": int(start_time),
        "endTime": int(end_time)
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Binance returned {response.status_code}: {response.text}")

    return response.json()


def process_binance_data(raw_data, symbol):
    candles = []
    for row in raw_data:
        try:
            candles.append({
                "timestamp": row[0],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "symbol": symbol,
                "start_time": row[0],
                "end_time": row[0] + 60000  # assuming 1-minute candles
            })
        except (IndexError, ValueError):
            continue
    return candles
