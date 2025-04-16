from ta.momentum import WilliamsRIndicator

def compute_williams(df, params):
    try:
        period = int(params.get("period", 14))
    except (ValueError, TypeError):
        raise ValueError("Invalid 'period' for Williams %R")
    willr = WilliamsRIndicator(high=df["high"], low=df["low"], close=df["close"], lbp=period)
    return {"williams_r": willr.williams_r().iloc[-1]}
