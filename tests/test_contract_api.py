import pytest
from fastapi.testclient import TestClient
from services.indicator_api.main import app
from unittest.mock import patch

client = TestClient(app)

@pytest.mark.parametrize("invalid_payload, expected_status", [
    ({
        "interval": "1min",
        "indicators": {
            "rsi": {
                "start_time": "1744804680000",
                "end_time": "1744804920000",
                "params": {"window": 14}
            }
        }
    }, 422),

    ({
        "symbol": 12345,
        "interval": "1min",
        "indicators": {
            "rsi": {
                "start_time": "1744804680000",
                "end_time": "1744804920000",
                "params": {"window": 14}
            }
        }
    }, 422),

    ({
        "symbol": "BTCUSDT",
        "interval": "1min"
    }, 422),

    ({
        "symbol": "BTCUSDT",
        "interval": "1min",
        "indicators": {}
    }, 400),

    ({
        "symbol": "BTCUSDT",
        "interval": "1min",
        "indicators": {
            "rsi": {
                "start_time": "1744804680000",
                "end_time": "1744804920000",
                "params": {"window": "not_an_int"}
            }
        }
    }, 422),

    ({
        "symbol": "BTCUSDT",
        "interval": "1min",
        "extra_field": "not allowed",
        "indicators": {
            "rsi": {
                "start_time": "1744804680000",
                "end_time": "1744804920000",
                "params": {"window": 14}
            }
        }
    }, 422),

    ({
        "symbol": "BTCUSDT",
        "interval": "1min",
        "indicators": {
            "rsi": {
                "start_time": "invalid",  # this will be caught by Pydantic
                "end_time": "1744804920000",
                "params": {"window": 14}
            }
        }
    }, 422)
])

@patch("services.indicator_api.router.get_redis_client")
def test_field_validation_and_param_types(mock_redis, invalid_payload, expected_status):
    mock_redis.return_value.lrange.return_value = [
        '{"timestamp": 1744804680000, "open": 84000, "high": 84010, "low": 83990, "close": 84005, "volume": 5}'
    ]
    response = client.post("/indicators/calculate", json=invalid_payload)
    print(f"\n❗ STATUS: {response.status_code}\n❗ RESPONSE JSON: {response.json()}")
    assert response.status_code == expected_status
