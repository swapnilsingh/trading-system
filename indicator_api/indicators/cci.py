import ta

def compute_cci(df, params):
    window = params.get("window", 20)
    cci = ta.trend.CCIIndicator(
        high=df["high"], low=df["low"], close=df["close"], window=window
    )
    return {"cci": cci.cci().iloc[-1]}
