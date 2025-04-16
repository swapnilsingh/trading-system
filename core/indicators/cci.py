from ta.trend import CCIIndicator

def compute_cci(df, params):
    try:
        period = int(params.get("period", 20))
    except (ValueError, TypeError):
        raise ValueError("Invalid 'period' for CCI")
    cci = CCIIndicator(high=df["high"], low=df["low"], close=df["close"], window=period)
    return {"cci": cci.cci().iloc[-1]}
