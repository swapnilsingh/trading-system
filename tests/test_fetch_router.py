# tests/test_fetch_router.py

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.ohlcv_api.main import app
from pydantic import StrictStr

client = TestClient(app)


@pytest.fixture
def ohlcv_client():
    return client

@pytest.fixture(autouse=True)
def mock_redis_and_binance():
    with patch("services.ohlcv_api.fetch_router.fetch_ohlcv_range") as mock_redis, \
         patch("services.ohlcv_api.fetch_router.save_ohlcv_batch") as mock_save:
        yield mock_redis, mock_save

def test_fetch_from_redis_only(mock_redis_and_binance):
    mock_redis, _ = mock_redis_and_binance
    mock_redis.return_value = [
        {
            "timestamp": 1744804680000,
            "open": 84000,
            "high": 84010,
            "low": 83990,
            "close": 84005,
            "volume": 5,
            "symbol": "BTCUSDT"
        }
    ]

    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("📦 Redis Response:", response.status_code, response.json())
    assert response.status_code == 200
    assert response.json()["source"] == "redis"


@patch("services.ohlcv_api.fetch_router.requests.get")
def test_fallback_to_binance(mock_requests_get, mock_redis_and_binance):
    mock_redis, mock_save = mock_redis_and_binance
    mock_redis.return_value = []

    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = [
        [
            1744804680000, "84000", "84010", "83990", "84005", "5", "", "", "", "", "", ""
        ]
    ]

    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("🌐 Binance Fallback:", response.status_code, response.json())
    assert response.status_code == 200
    assert response.json()["source"] == "binance"
    mock_save.assert_called_once()


@patch("services.ohlcv_api.fetch_router.requests.get")
def test_binance_failure(mock_requests_get, mock_redis_and_binance):
    mock_redis, _ = mock_redis_and_binance
    mock_redis.return_value = []
    mock_requests_get.return_value.status_code = 500

    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("❌ Binance Failure:", response.status_code, response.json())
    assert response.status_code == 502

def test_fetch_missing_symbol():
    payload = {
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("🚫 Missing Symbol:", response.status_code, response.json())
    assert response.status_code == 422

def test_fetch_invalid_symbol_type():
    payload = {
        "symbol": 1234,
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("🚫 Invalid Symbol Type:", response.status_code, response.json())
    assert response.status_code in [400, 422]

@patch("services.ohlcv_api.fetch_router.requests.get")
def test_fetch_missing_time_range(mock_requests_get, mock_redis_and_binance):
    mock_redis, mock_save = mock_redis_and_binance
    mock_redis.return_value = []

    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = [
        [1744804680000, "84000", "84010", "83990", "84005", "5", "", "", "", "", "", ""]
    ]

    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min"
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("⏳ Missing Time Range:", response.status_code, response.json())
    assert response.status_code == 200
    assert response.json()["source"] == "binance"

def test_fetch_missing_interval():
    payload = {
        "symbol": "BTCUSDT",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("🚫 Missing Interval:", response.status_code, response.json())
    assert response.status_code == 422

def test_fetch_invalid_time_format():
    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "start_time": "notatime",
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("🚫 Invalid Start Time:", response.status_code, response.json())
    assert response.status_code == 422

def test_fetch_empty_interval():
    payload = {
        "symbol": "BTCUSDT",
        "interval": "",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("🚫 Empty Interval:", response.status_code, response.json())
    assert response.status_code == 422

def test_fetch_uppercase_symbol():
    payload = {
        "symbol": "btcusdt",
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("🔠 Lowercase Symbol Test:", response.status_code, response.json())
    assert response.status_code in [200, 404]

@patch("services.ohlcv_api.fetch_router.requests.get")
def test_invalid_interval_format(mock_requests_get, mock_redis_and_binance):
    mock_redis, mock_save = mock_redis_and_binance
    mock_redis.return_value = []

    mock_requests_get.return_value.status_code = 502

    payload = {
        "symbol": "BTCUSDT",
        "interval": "1wrong",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    print("🚫 Invalid Interval Format:", response.status_code, response.json())
    assert response.status_code == 502
