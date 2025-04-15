import ta

def compute_ema(df, params):
    window = params.get("window", 20)
    return {"ema": ta.trend.EMAIndicator(close=df["close"], window=window).ema_indicator().iloc[-1]}
