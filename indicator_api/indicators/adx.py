import ta

def compute_adx(df, params):
    window = params.get("window", 14)
    adx = ta.trend.ADXIndicator(
        high=df["high"], low=df["low"], close=df["close"], window=window
    )
    return {"adx": adx.adx().iloc[-1]}
