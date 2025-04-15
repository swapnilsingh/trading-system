import ta

def compute_williams(df, params):
    window = params.get("window", 14)
    willr = ta.momentum.WilliamsRIndicator(
        high=df["high"], low=df["low"], close=df["close"], lbp=window
    )
    return {"williams_r": willr.williams_r().iloc[-1]}
