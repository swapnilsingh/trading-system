def compute_sma(df, params):
    try:
        period = int(params.get("period", 20))
    except (ValueError, TypeError):
        raise ValueError("Invalid 'period' for SMA")
    return {"sma": df["close"].rolling(window=period).mean().iloc[-1]}
