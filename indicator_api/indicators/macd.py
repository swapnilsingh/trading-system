# indicator_api.indicators/macd.py
from ta.trend import MACD

def compute_macd(df, params):
    macd = MACD(
        close=df["close"],
        window_slow=params.get("slow", 26),
        window_fast=params.get("fast", 12),
        window_sign=params.get("signal", 9)
    )
    return {
        "macd": macd.macd().iloc[-1],
        "macd_signal": macd.macd_signal().iloc[-1]
    }
