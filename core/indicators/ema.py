def compute_ema(df, params):
    try:
        period = int(params.get("period", 20))
    except (ValueError, TypeError):
        raise ValueError("Invalid 'period' for EMA")
    return {"ema": df["close"].ewm(span=period, adjust=False).mean().iloc[-1]}
