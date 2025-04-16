from ta.momentum import RSIIndicator

def compute_rsi(df, params):
    try:
        window = int(params.get("period", 14))
    except (ValueError, TypeError):
        raise ValueError("Invalid 'period' for RSI")
    rsi = RSIIndicator(close=df["close"], window=window)
    return {"rsi": rsi.rsi().iloc[-1]}
