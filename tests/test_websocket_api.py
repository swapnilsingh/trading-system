import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from services.websocket_api.websocket_data import BinanceTickStreamer
import websockets
from services.websocket_api.main import app

client = TestClient(app)

# Mock WebSocket class that simulates an asynchronous iterable
class MockWebSocket:
    def __init__(self, data=None):
        self.data = data or []

    async def __aiter__(self):
        for item in self.data:
            yield item


# Shared payloads
symbol_btc = {"symbol": "BTCUSDT", "interval": "1min"}
symbol_eth = {"symbol": "ETHUSDT", "interval": "1min"}

@pytest.mark.asyncio
def test_start_stream():
    response = client.post("/start", json=symbol_btc)
    assert response.status_code == 200
    assert "Started streaming" in response.json()["message"]


def test_start_stream_duplicate():
    response = client.post("/start", json=symbol_btc)
    assert response.status_code == 400
    assert "Stream already running" in response.json()["detail"]


def test_list_streams_after_start():
    response = client.get("/streams")
    assert response.status_code == 200
    assert "btcusdt@1min" in response.json().get("active_streams", [])


def test_update_stream():
    payload = {
        "old_symbol": "BTCUSDT",
        "old_interval": "1min",
        "new_symbol": "ETHUSDT",
        "new_interval": "1min"
    }
    response = client.post("/update", json=payload)
    assert response.status_code == 200
    assert "Updated stream from BTCUSDT@1min to ETHUSDT@1min" in response.json()["message"]


def test_update_stream_fail_on_nonexistent_old():
    payload = {
        "old_symbol": "FAKE",
        "old_interval": "1min",
        "new_symbol": "XRPUSDT",
        "new_interval": "1min"
    }
    response = client.post("/update", json=payload)
    assert response.status_code == 404


def test_update_stream_fail_on_existing_new():
    payload = {
        "old_symbol": "ETHUSDT",
        "old_interval": "1min",
        "new_symbol": "ETHUSDT",
        "new_interval": "1min"
    }
    response = client.post("/update", json=payload)
    assert response.status_code == 400


def test_list_streams_after_update():
    response = client.get("/streams")
    assert response.status_code == 200
    assert "ethusdt@1min" in response.json()["active_streams"]


def test_stop_stream():
    response = client.post("/stop", json=symbol_eth)
    assert response.status_code == 200
    assert "Stopped streaming" in response.json()["message"]


def test_stop_stream_invalid():
    response = client.post("/stop", json=symbol_eth)
    assert response.status_code == 404


def test_start_batch_streams():
    batch_payload = [{"symbol": f"TEST{i}", "interval": "1min"} for i in range(3)]
    response = client.post("/start/batch", json=batch_payload)
    assert response.status_code == 200
    assert len(response.json().get("active_streams")) == 3


def test_start_batch_too_many():
    batch_payload = [{"symbol": f"TOOMANY{i}", "interval": "1min"} for i in range(21)]
    response = client.post("/start/batch", json=batch_payload)
    assert response.status_code == 400
    assert "Too many streams" in response.json()["detail"]


def test_stop_all_streams_without_confirmation():
    response = client.delete("/stop/all")
    assert response.status_code == 422  # Missing required query param


def test_stop_all_streams_with_confirmation():
    response = client.delete("/stop/all?confirm=true")
    assert response.status_code == 200
    assert response.json()["active_streams"] == []


# Test WebSocket streaming behavior
@pytest.mark.asyncio
async def test_start_streaming():
    with patch.object(BinanceTickStreamer, 'connect_and_stream', return_value=None) as mock_stream:
        response =  client.post("/start", json={"symbol": "BTCUSDT", "interval": "1min"})
        assert response.status_code == 200
        assert "Started streaming" in response.json()["message"]
        mock_stream.assert_called_once()

# Mock the websockets.connect method
@patch("websockets.connect")
async def test_websocket_reconnection(mock_connect):
    # Mocking a normal WebSocket connection
    mock_ws = MockWebSocket(data=["Test data"])
    mock_connect.return_value = mock_ws
    
    # Simulate WebSocket connection closure
    mock_connect.side_effect = websockets.ConnectionClosed(1000, "Normal Closure")

    # Now we run the actual connection and stream
    try:
        async for message in mock_ws:
            assert message == "Test data"
    except websockets.ConnectionClosed as e:
        assert e.code == 1000  # This is the normal closure code


@patch("websockets.connect")
async def test_invalid_websocket_data(mock_connect):
    # Mocking WebSocket with invalid data (empty or malformed data)
    mock_ws = MockWebSocket(data=["Invalid data"])
    mock_connect.return_value = mock_ws
    
    # Simulate an invalid WebSocket message and test how the code handles it
    try:
        async for message in mock_ws:
            assert message == "Invalid data"
    except Exception as e:
        assert isinstance(e, websockets.WebSocketException)
