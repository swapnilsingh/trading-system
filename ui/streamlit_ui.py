import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import time
import requests
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objs as go

from utils.redis_queue import get_redis_client, get_ohlcv_key
from utils.data_utils import parse_ohlcv_list

# Constants
SYMBOL = "BTCUSDT"
INTERVAL = "1min"
INDICATOR_API = "http://localhost:8000/indicator/calculate"
CATALOG_API = "http://localhost:8000/indicator/catalog"

redis_client = get_redis_client()

def fetch_indicator_data(df):
    if df.empty:
        return {}

    start_ts = int(df["timestamp"].min().timestamp() * 1000)
    end_ts = int(df["timestamp"].max().timestamp() * 1000)

    payload = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "indicators": {}
    }

    try:
        catalog_resp = requests.get(CATALOG_API, timeout=5)
        catalog = catalog_resp.json().get("indicators", {})
        for name, meta in catalog.items():
            payload["indicators"][name] = {
                "start_time": start_ts,
                "end_time": end_ts,
                "params": meta.get("default_params", {})
            }

        resp = requests.post(INDICATOR_API, json=payload, timeout=15)
        return resp.json()

    except Exception as e:
        st.error(f"❌ Error fetching indicators: {e}")
        return {}

def app():
    st.set_page_config(page_title="BTC/USDT Live Chart", layout="wide")
    st.title(f"📈 BTC/USDT Multi-Indicator Chart ({INTERVAL})")

    redis_key = get_ohlcv_key(SYMBOL, INTERVAL)
    raw_data = redis_client.lrange(redis_key, 0, -1)
    df = parse_ohlcv_list(raw_data)

    if df.empty:
        st.warning("⚠️ No OHLCV data found.")
        return

    df["timestamp"] = pd.to_datetime(df["start_time"], unit="ms")

    # Create 4-row subplot layout
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.4, 0.15, 0.2, 0.25],
        specs=[[{"type": "xy"}], [{"type": "bar"}], [{"type": "xy"}], [{"type": "xy"}]],
        subplot_titles=("Candles + Indicators", "Volume", "RSI", "MACD")
    )

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df["timestamp"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Candles",
        increasing_line_color="green",
        decreasing_line_color="red"
    ), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(
        x=df["timestamp"],
        y=df["volume"],
        name="Volume",
        marker_color="rgba(128,128,255,0.5)"
    ), row=2, col=1)

    # Fetch indicators and distribute
    indicators = fetch_indicator_data(df)
    for name, values in indicators.items():
        if not values or not isinstance(values, dict):
            continue

        for key, series in values.items():
            if not isinstance(series, list) or len(series) != len(df):
                continue

            y = series
            x = df["timestamp"]

            if name.lower() in ["rsi"]:
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="RSI"), row=3, col=1)

            elif name.lower() in ["macd"]:
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="MACD", line=dict(color="blue")), row=4, col=1)
            elif name.lower() in ["macd_signal"]:
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Signal", line=dict(color="red")), row=4, col=1)
            elif name.lower() in ["macd_hist"]:
                fig.add_trace(go.Bar(x=x, y=y, name="MACD Histogram"), row=4, col=1)
            else:
                # Default: overlay indicators (e.g., SMA, EMA, Bollinger Bands)
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=f"{name.upper()} ({key})"), row=1, col=1)

    fig.update_layout(
        template="plotly_white",
        height=1000,
        showlegend=True,
        title="📊 BTC/USDT Live Candlestick Chart with Volume and Indicators",
        xaxis=dict(title="Time"),
        yaxis=dict(title="Price"),
        legend=dict(orientation="h", y=1.03, x=0.5, xanchor="center", yanchor="bottom"),
        margin=dict(t=70, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.write("🕯️ Latest Candle", df.iloc[-1].to_dict())

if __name__ == "__main__":
    app()
