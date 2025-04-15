# indicator_api/bollinger.py
from ta.volatility import BollingerBands

def compute_bollinger(df, params):
    bb = BollingerBands(
        close=df["close"],
        window=params.get("window", 20),
        window_dev=params.get("std", 2.0)
    )
    return {
        "bollinger_upper": bb.bollinger_hband().iloc[-1],
        "bollinger_lower": bb.bollinger_lband().iloc[-1],
        "bollinger_middle": bb.bollinger_mavg().iloc[-1]
    }
