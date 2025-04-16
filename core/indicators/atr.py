from ta.volatility import AverageTrueRange

def compute_atr(df, params):
    try:
        period = int(params.get("period", 14))
    except (ValueError, TypeError):
        raise ValueError("Invalid 'period' for ATR")
    atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=period)
    return {"atr": atr.average_true_range().iloc[-1]}
