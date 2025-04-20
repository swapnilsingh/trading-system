import requests
import time

INDICATOR_API = "http://indicator-api:8000"

def wait_for_service(url, timeout=30):
    for _ in range(timeout):
        try:
            response = requests.get(f"{url}/indicators/catalog")
            if response.status_code == 200:
                print("✅ indicator-api is up")
                return
        except requests.exceptions.ConnectionError:
            pass
        print("⏳ Waiting for indicator-api to become available...")
        time.sleep(1)
    raise Exception("❌ indicator-api did not become available in time")

def test_end_to_end_indicator_flow():
    wait_for_service(INDICATOR_API)

    end_time = 1745172750354
    start_time = 1745165550354

    indicator_payload = {
        "symbol": "BTCUSDT",
        "interval": "1m",
        "indicators": {
            "sma": {
                "start_time": str(start_time),
                "end_time": str(end_time),
                "params": {"period": 5}
            }
        }
    }

    response = requests.post(f"{INDICATOR_API}/indicators/calculate", json=indicator_payload)
    assert response.status_code == 200, f"❌ Indicator failed: {response.text}"

    result = response.json()
    assert "sma" in result, "❌ SMA result missing in response"
    assert "sma" in result["sma"], "❌ SMA value not computed"
    print("✅ SMA indicator test passed")
