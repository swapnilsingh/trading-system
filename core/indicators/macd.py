from ta.trend import MACD

def compute_macd(df, params):
    try:
        slow = int(params.get("slow", 26))
        fast = int(params.get("fast", 12))
        signal = int(params.get("signal", 9))
    except (ValueError, TypeError):
        raise ValueError("Invalid MACD parameters")
    macd = MACD(close=df["close"], window_slow=slow, window_fast=fast, window_sign=signal)
    return {
        "macd": macd.macd().iloc[-1],
        "macd_signal": macd.macd_signal().iloc[-1]
    }
