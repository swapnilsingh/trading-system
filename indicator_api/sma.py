# indicator_api/sma.py

def compute_sma(df, window):
    return {f"sma{window}": df["close"].rolling(window=window).mean().iloc[-1]}
