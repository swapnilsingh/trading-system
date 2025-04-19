# tests/test_redis_queue.py
import json
import pytest
from unittest.mock import MagicMock, patch
from utils import redis_queue
from utils.redis_queue import push_to_queue, pop_from_queue



@pytest.fixture
def mock_redis():
    client = MagicMock()
    client.rpush = MagicMock()
    client.lpop = MagicMock(return_value=json.dumps({"foo": "bar"}))
    client.blpop = MagicMock(return_value=("test", json.dumps({"foo": "bar"})))
    client.expire = MagicMock()
    client.llen = MagicMock(return_value=1)
    client.lrange = MagicMock(return_value=[json.dumps({
        "symbol": "BTCUSDT", "timestamp": 1713532800000
    })])
    client.delete = MagicMock()
    client.lindex = MagicMock(return_value=json.dumps({
        "symbol": "BTCUSDT", "close": 105
    }))
    return client

def test_push_to_queue(mock_redis):
    redis_queue.push_to_queue(mock_redis, "test_key", {"foo": "bar"}, ttl=10)
    mock_redis.rpush.assert_called_once()
    mock_redis.expire.assert_called_once()

def test_save_ohlcv_batch(mock_redis):
    data = [{
        "symbol": "BTCUSDT", "open": 1, "high": 1, "low": 1,
        "close": 1, "volume": 1, "start_time": 1, "end_time": 2
    }]
    redis_queue.save_ohlcv_batch(mock_redis, "BTCUSDT", "1min", data)
    assert mock_redis.rpush.called

def test_fetch_ohlcv_range(mock_redis):
    results = redis_queue.fetch_ohlcv_range(mock_redis, "BTCUSDT", "1min", 1713532790000, 1713532810000)
    assert isinstance(results, list)
    assert results[0]["timestamp"] == 1713532800000

def test_clear_ohlcv(mock_redis):
    redis_queue.clear_ohlcv(mock_redis, "BTCUSDT", "1min")
    mock_redis.delete.assert_called_once()

def test_get_latest_ohlcv(mock_redis):
    result = redis_queue.get_latest_ohlcv(mock_redis, "BTCUSDT", "1min")
    assert result["close"] == 105

# Test: Push to Redis Queue
@patch("utils.redis_queue.get_redis_client")
def test_push_to_queue(mock_redis_client):
    mock_redis = MagicMock()
    mock_redis_client.return_value = mock_redis

    push_to_queue(mock_redis, "test_key", {"foo": "bar"})
    
    mock_redis.rpush.assert_called_with("test_key", '{"foo": "bar"}')

# Test: Pop from Redis Queue
@patch("utils.redis_queue.get_redis_client")
def test_pop_from_queue(mock_redis_client):
    mock_redis = MagicMock()
    mock_redis_client.return_value = mock_redis
    mock_redis.lpop.return_value = '{"foo": "bar"}'

    result = pop_from_queue(mock_redis, "test_key")
    assert result == '{"foo": "bar"}'
    mock_redis.lpop.assert_called_with("test_key")
