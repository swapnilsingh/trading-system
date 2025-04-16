import yaml
import os

def load_config(path="config/config.yaml"):
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    # 🔁 Override Redis host with env variable if present
    redis_host_env = os.getenv("REDIS_HOST")
    if redis_host_env:
        config.setdefault("redis", {})  # ensure redis key exists
        config["redis"]["host"] = redis_host_env

    return config
