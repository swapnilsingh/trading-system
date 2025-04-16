# conftest.py
import pytest
from unittest.mock import patch

MOCK_OHLCV_SAMPLE = [
    '{"timestamp": 1744804680000, "open": 84000, "high": 84010, "low": 83990, "close": 84005, "volume": 5}'
]

@pytest.fixture
def mock_redis():
    with patch("services.indicator_api.router.get_redis_client") as mock:
        mock.return_value.lrange.return_value = MOCK_OHLCV_SAMPLE
        yield mock
