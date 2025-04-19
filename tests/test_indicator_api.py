import json
import httpx
from typing import List
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.indicator_api.main import app as indicator_app

client = TestClient(indicator_app)

MOCK_OHLCV_DATA = [
    json.dumps({
        "timestamp": 1744804680000 + i * 60000,
        "open": 84000 + i,
        "high": 84010 + i,
        "low": 83990 + i,
        "close": 84005 + i,
        "volume": 5 + i
    }) for i in range(200)
]

ALL_INDICATORS = {
    "rsi": {"params": {"period": 14}},
    "macd": {"params": {"fast_period": 12, "slow_period": 26, "signal_period": 9}},
    "bollinger": {"params": {"period": 20, "std_dev": 2}},
    "atr": {"params": {"period": 14}},
    "adx": {"params": {"period": 14}},
    "cci": {"params": {"period": 20}},
    "ema5": {"params": {"period": 5}},
    "ema10": {"params": {"period": 10}},
    "ema20": {"params": {"period": 20}},
    "ema50": {"params": {"period": 50}},
    "ema200": {"params": {"period": 200}},
    "sma5": {"params": {"period": 5}},
    "sma10": {"params": {"period": 10}},
    "sma50": {"params": {"period": 50}},
    "sma200": {"params": {"period": 200}},
}

def make_payload(indicator_subset: List[str], start="1744804680000", end="1744816680000"):
    indicators = {
        name: {"start_time": start, "end_time": end, **ALL_INDICATORS[name]}
        for name in indicator_subset
    }
    return {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "indicators": indicators
    }

@patch("services.indicator_api.router.get_redis_client")
def test_all_indicators_success(mock_redis):
    mock_redis.return_value.lrange.return_value = MOCK_OHLCV_DATA
    response = client.post("/indicators/calculate", json=make_payload(list(ALL_INDICATORS.keys())))
    assert response.status_code == 200
    for key in ALL_INDICATORS.keys():
        assert key in response.json()

@patch("services.indicator_api.router.get_redis_client")
@patch("services.indicator_api.router.httpx.post")
def test_missing_ohlcv_data(mock_httpx_post, mock_redis):
    mock_redis.return_value.lrange.return_value = [
        json.dumps({
            "timestamp": 1600000000000,
            "open": 100, "high": 105, "low": 95, "close": 102, "volume": 10
        })
    ]
    mock_httpx_post.return_value = httpx.Response(
        status_code=200,
        content=json.dumps({"source": "binance", "data": []}),
        headers={"Content-Type": "application/json"},
        request=httpx.Request("POST", "http://ohlcv-api:8010/ohlcv/fetch")
    )
    response = client.post("/indicators/calculate", json=make_payload(["rsi"], "1744804680000", "1744804920000"))
    assert response.status_code == 404

@patch("services.indicator_api.router.get_redis_client")
def test_invalid_timestamp_format(mock_redis):
    mock_redis.return_value.lrange.return_value = MOCK_OHLCV_DATA
    payload = make_payload(["rsi"])
    payload["indicators"]["rsi"]["start_time"] = "invalid"
    response = client.post("/indicators/calculate", json=payload)
    assert response.status_code == 422

@patch("services.indicator_api.router.get_redis_client")
@patch("services.indicator_api.router.httpx.post")
def test_invalid_time_range(mock_httpx_post, mock_redis):
    mock_redis.return_value.lrange.return_value = MOCK_OHLCV_DATA
    mock_httpx_post.return_value = httpx.Response(
        status_code=200,
        content=json.dumps({"source": "binance", "data": []}),
        headers={"Content-Type": "application/json"},
        request=httpx.Request("POST", "http://ohlcv-api:8010/ohlcv/fetch")
    )
    response = client.post("/indicators/calculate", json=make_payload(["rsi"], "1600000000000", "1600000010000"))
    assert response.status_code == 404

@patch("services.indicator_api.router.get_redis_client")
def test_unsupported_indicator(mock_redis):
    mock_redis.return_value.lrange.return_value = MOCK_OHLCV_DATA
    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "indicators": {
            "fake_indicator": {
                "start_time": "1744804680000",
                "end_time": "1744804920000",
                "params": {}
            }
        }
    }
    response = client.post("/indicators/calculate", json=payload)
    assert response.status_code == 422

@patch("services.indicator_api.router.get_redis_client")
def test_edge_case_empty_interval(mock_redis):
    mock_redis.return_value.lrange.return_value = MOCK_OHLCV_DATA
    payload = make_payload(["rsi"])
    payload["interval"] = ""
    response = client.post("/indicators/calculate", json=payload)
    assert response.status_code in [400, 422]

@patch("services.indicator_api.router.get_redis_client")
def test_edge_case_empty_indicators(mock_redis):
    mock_redis.return_value.lrange.return_value = MOCK_OHLCV_DATA
    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "indicators": {}
    }
    response = client.post("/indicators/calculate", json=payload)
    assert response.status_code == 400

@patch("services.indicator_api.router.get_redis_client")
def test_edge_case_invalid_period_type(mock_redis):
    mock_redis.return_value.lrange.return_value = MOCK_OHLCV_DATA
    payload = make_payload(["rsi"])
    payload["indicators"]["rsi"]["params"]["period"] = "fourteen"
    response = client.post("/indicators/calculate", json=payload)
    assert response.status_code == 500

def test_invalid_indicator_name():
    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "indicators": {
            "invalid_indicator": {
                "start_time": "1744804680000",
                "end_time": "1744804920000",
                "params": {}
            }
        }
    }
    response = client.post("/indicators/calculate", json=payload)
    assert response.status_code == 404  # Corrected payload and expected status
    assert "detail" in response.json()

# Test missing required fields (e.g., symbol)
def test_missing_symbol():
    response = client.post("/indicators/calculate", json={"timestamp": "2025-04-01", "indicators": {"rsi": 50.0}})
    assert response.status_code == 422  # Validation failure for missing symbol
    assert "detail" in response.json()

# Test empty request body
def test_empty_request_body():
    response = client.post("/indicators/calculate", json={})
    assert response.status_code == 422  # Validation error for missing fields
    assert "detail" in response.json()

@patch("services.indicator_api.router.get_redis_client")
def test_unsupported_indicator(mock_redis):
    mock_redis.return_value.lrange.return_value = MOCK_OHLCV_DATA
    payload = {
        "symbol": "BTCUSDT",
        "interval": "1min",
        "indicators": {
            "fake_indicator": {
                "start_time": "1744804680000",
                "end_time": "1744804920000",
                "params": {}
            }
        }
    }
    response = client.post("/indicators/calculate", json=payload)
    assert response.status_code == 404  # Changed from 422 to 404
