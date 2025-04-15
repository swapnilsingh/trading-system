# indicator_api.indicators/rsi.py
from ta.momentum import RSIIndicator

def compute_rsi(df, params):
    window = params.get("window", 14)
    rsi = RSIIndicator(close=df["close"], window=window)
    return {"rsi": rsi.rsi().iloc[-1]}
