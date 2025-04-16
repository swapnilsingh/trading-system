from ta.trend import ADXIndicator

def compute_adx(df, params):
    try:
        period = int(params.get("period", 14))
    except (ValueError, TypeError):
        raise ValueError("Invalid 'period' for ADX")
    adx = ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=period)
    return {"adx": adx.adx().iloc[-1]}
