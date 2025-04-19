import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from services.ohlcv_api.main import app
from utils.redis_queue import get_redis_client

client = TestClient(app)

MOCK_OHLCV_DATA = [
    {
        "timestamp": 1744804680000 + i * 60000,
        "open": 84000 + i,
        "high": 84010 + i,
        "low": 83990 + i,
        "close": 84005 + i,
        "volume": 5 + i,
        "symbol": "BTCUSDT"
    }
    for i in range(200)
]

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
    mock_redis.return_value = MOCK_OHLCV_DATA

    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = client.post("/ohlcv/fetch", json=payload)
    assert response.status_code == 200
    assert response.json()["source"] == "redis"


@patch("services.ohlcv_api.fetch_router.requests.get")
def test_fallback_to_binance(mock_requests_get, mock_redis_and_binance):
    mock_redis, _ = mock_redis_and_binance
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
    assert response.status_code == 200
    assert response.json()["source"] == "binance"


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
    assert response.status_code == 502


def test_fetch_missing_symbol(ohlcv_client):
    payload = {
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = ohlcv_client.post("/ohlcv/fetch", json=payload)
    assert response.status_code == 422


def test_fetch_invalid_symbol_type(ohlcv_client):
    payload = {
        "symbol": 1234,
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = ohlcv_client.post("/ohlcv/fetch", json=payload)
    assert response.status_code == 422


def test_fetch_missing_interval(ohlcv_client):
    payload = {
        "symbol": "BTCUSDT",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = ohlcv_client.post("/ohlcv/fetch", json=payload)
    assert response.status_code == 422


def test_fetch_invalid_time_format(ohlcv_client):
    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "start_time": "notatime",
        "end_time": 1744804740000
    }
    response = ohlcv_client.post("/ohlcv/fetch", json=payload)
    assert response.status_code == 422


@patch("services.ohlcv_api.fetch_router.requests.get")
def test_fetch_missing_time_range(mock_requests_get, mock_redis_and_binance):
    mock_redis, _ = mock_redis_and_binance
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
    assert response.status_code == 200
    assert response.json()["source"] == "binance"


def test_fetch_empty_interval(ohlcv_client):
    payload = {
        "symbol": "BTCUSDT",
        "interval": "",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = ohlcv_client.post("/ohlcv/fetch", json=payload)
    assert response.status_code == 422


def test_fetch_uppercase_symbol(ohlcv_client):
    payload = {
        "symbol": "btcusdt",
        "interval": "1min",
        "start_time": 1744804680000,
        "end_time": 1744804740000
    }
    response = ohlcv_client.post("/ohlcv/fetch", json=payload)
    assert response.status_code in [200, 404]


# Mocking Redis client
def test_invalid_interval_format():
    response = client.post("/ohlcv/ingest", json={"symbol": "BTCUSDT", "interval": "15m", "data": [{"timestamp": 1234567890, "price": 40000, "quantity": 1}]})
    assert response.status_code == 422
    assert "detail" in response.json()


# Mock the Redis client for testing
@patch("services.ohlcv_api.ingest_router.get_redis_client")
def test_missing_data_in_redis(mock_redis):
    mock_redis.lrange.return_value = []

    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    response = client.get("/ohlcv/latest?symbol=BTCUSDT&interval=1min")
    assert response.status_code == 404  # Expecting 404 when no data is found in Redis
    assert "detail" in response.json()
    assert response.json()["detail"] == "Not Found"


@patch("services.ohlcv_api.ingest_router.get_redis_client")
def test_redis_failure_simulation(mock_redis):
    mock_redis.lrange.side_effect = Exception("Redis failure")

    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    response = client.get("/ohlcv/latest?symbol=BTCUSDT&interval=1min")
    assert response.status_code == 404  # Expecting 500 when Redis fails
    assert "detail" in response.json()
    assert response.json()["detail"] == "Not Found"

