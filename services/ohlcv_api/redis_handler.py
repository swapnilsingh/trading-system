# redis_handler.py
import redis
import json
from utils.config import load_config

# Connect to Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

def save_data_to_redis(key, data):
    """Save data to Redis."""
    for item in data:
        redis_client.lpush(key, json.dumps(item))

def fetch_data_from_redis(key):
    """Fetch data from Redis."""
    data = []
    raw_data = redis_client.lrange(key, 0, -1)
    for item in raw_data:
        data.append(json.loads(item))
    return data
