# indicator_api/atr.py
from ta.volatility import AverageTrueRange

def compute_atr(df, params):
    window = params.get("window", 14)
    atr = AverageTrueRange(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        window=window
    )
    return {"atr": atr.average_true_range().iloc[-1]}
