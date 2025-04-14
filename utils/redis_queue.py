# utils/redis_queue.py
import redis
import yaml
from typing import Any, Optional


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
    client.rpush(key, value)
    if ttl:
        client.expire(key, ttl)


def pop_from_queue(client: redis.Redis, key: str, block: bool = False, timeout: int = 5) -> Optional[str]:
    if block:
        result = client.blpop(key, timeout=timeout)
        return result[1] if result else None
    else:
        return client.lpop(key)


if __name__ == "__main__":
    cfg = load_config()
    client = get_redis_client(cfg)

    # Push test
    push_to_queue(client, "test:queue", "hello world", ttl=20)
    print("✅ Pushed: 'hello world' to test:queue (expires in 20s)")

    # Pop test
    result = pop_from_queue(client, "test:queue", block=False)
    print(f"📥 Popped: {result}")

