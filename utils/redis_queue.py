# utils/redis_queue.py
import redis
import yaml
import json
from typing import Any, Optional, List, Dict
from utils.config import load_config
from utils.schemas import format_ohlcv_data


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_redis_client(config: Optional[dict] = None) -> redis.Redis:
    if config is None:
        config = load_config()
    redis_cfg = config.get("redis", {})
    return redis.Redis(
        host=redis_cfg.get("host", "localhost"),
        port=redis_cfg.get("port", 6379),
        db=redis_cfg.get("db", 0),
        decode_responses=redis_cfg.get("decode_responses", True),
    )


def push_to_queue(client: redis.Redis, key: str, value: Any, ttl: Optional[int] = None):
    try:
        serialized = json.dumps(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"❌ Cannot serialize value for Redis: {e}")
    client.rpush(key, serialized)
    if ttl:
        client.expire(key, ttl)


def pop_from_queue(client: redis.Redis, key: str, block: bool = False, timeout: int = 5) -> Optional[str]:
    if block:
        result = client.blpop(key, timeout=timeout)
        return result[1] if result else None
    else:
        return client.lpop(key)


# OHLCV Handling
config = load_config()
REDIS_KEY_TEMPLATE = config["redis"].get("ohlcv_key_template", "ohlcv:{symbol}:{interval}")

def get_ohlcv_key(symbol: str, interval: str) -> str:
    return REDIS_KEY_TEMPLATE.format(symbol=symbol.upper(), interval=interval)

def save_ohlcv_batch(
    redis_client: redis.Redis,
    symbol: str,
    interval: str,
    ohlcv_data: List[Dict[str, Any]],
    max_candles: int = 500
) -> None:
    redis_key = get_ohlcv_key(symbol, interval)
    for row in ohlcv_data:
        formatted = format_ohlcv_data(row)
        redis_client.rpush(redis_key, json.dumps(formatted))
    redis_client.ltrim(redis_key, -max_candles, -1)

def fetch_ohlcv_range(
    redis_client: redis.Redis,
    symbol: str,
    interval: str,
    start_ts: int,
    end_ts: int
) -> List[Dict[str, Any]]:
    redis_key = get_ohlcv_key(symbol, interval)
    all_candles = redis_client.lrange(redis_key, 0, -1)
    filtered = []
    for entry in all_candles:
        try:
            candle = json.loads(entry)
            if start_ts <= candle["timestamp"] <= end_ts:
                filtered.append(candle)
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    return filtered

def clear_ohlcv(redis_client: redis.Redis, symbol: str, interval: str) -> None:
    redis_client.delete(get_ohlcv_key(symbol, interval))

def get_latest_ohlcv(redis_client: redis.Redis, symbol: str, interval: str) -> Optional[Dict[str, Any]]:
    redis_key = get_ohlcv_key(symbol, interval)
    latest = redis_client.lindex(redis_key, -1)
    if latest is None:
        return None
    try:
        return json.loads(latest)
    except json.JSONDecodeError:
        return None
