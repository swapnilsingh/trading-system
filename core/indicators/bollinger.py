from ta.volatility import BollingerBands

def compute_bollinger(df, params):
    try:
        period = int(params.get("period", 20))
        std_dev = float(params.get("std_dev", 2))
    except (ValueError, TypeError):
        raise ValueError("Invalid Bollinger Band parameters")
    bb = BollingerBands(close=df["close"], window=period, window_dev=std_dev)
    return {
        "bollinger_mavg": bb.bollinger_mavg().iloc[-1],
        "bollinger_hband": bb.bollinger_hband().iloc[-1],
        "bollinger_lband": bb.bollinger_lband().iloc[-1],
    }
