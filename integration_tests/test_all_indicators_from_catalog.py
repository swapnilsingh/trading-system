import requests
import pytest
from datetime import datetime, timedelta

CATALOG_URL = "http://indicator-api:8000/indicators/catalog"

def pytest_generate_tests(metafunc):
    if "indicator_name" in metafunc.fixturenames and "indicator_meta" in metafunc.fixturenames:
        try:
            catalog = requests.get(CATALOG_URL, timeout=10)
            catalog.raise_for_status()
            data = catalog.json()["indicators"]
            params = [(name, meta) for name, meta in data.items()]
            metafunc.parametrize("indicator_name,indicator_meta", params)
        except Exception as e:
            pytest.skip(f"Catalog not ready: {e}")

def test_indicator_from_catalog(indicator_name, indicator_meta):
    symbol = "BTCUSDT"
    interval = "1m"
    now = datetime.utcnow()
    start_time = int((now - timedelta(minutes=100)).timestamp() * 1000)
    end_time = int(now.timestamp() * 1000)

    # Step 1: Ensure OHLCV exists
    ohlcv_resp = requests.post("http://ohlcv-api:8010/ohlcv/fetch", json={
        "symbol": symbol,
        "interval": interval,
        "start_time": start_time,
        "end_time": end_time
    })
    assert ohlcv_resp.status_code == 200, f"OHLCV fetch failed: {ohlcv_resp.text}"

    # Step 2: Compute indicator
    payload = {
        "symbol": symbol,
        "interval": interval,
        "indicators": {
            indicator_name: {
                "start_time": str(start_time),
                "end_time": str(end_time),
                "params": indicator_meta.get("default_params", {})
            }
        }
    }

    response = requests.post("http://indicator-api:8000/indicators/calculate", json=payload)
    assert response.status_code == 200, f"{indicator_name} failed: {response.text}"
    result = response.json()
    assert indicator_name in result, f"{indicator_name} missing in response"
