# utils/config.py
import yaml
import os

def load_config(path="config/config.yaml"):
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    # 🔁 Check and apply environment variable override
    redis_host_env = os.getenv("REDIS_HOST")
    if redis_host_env:
        config.setdefault("redis", {})
        config["redis"]["host"] = redis_host_env  # ✅ This is the key fix!

    return config
