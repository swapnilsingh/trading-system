# indicator_api.indicators/registry.py
from indicator_api.indicators.rsi import compute_rsi
from indicator_api.indicators.macd import compute_macd
from indicator_api.indicators.bollinger import compute_bollinger
from indicator_api.indicators.atr import compute_atr
from indicator_api.indicators.sma import compute_sma

registry = {
    "rsi": compute_rsi,
    "macd": compute_macd,
    "bollinger": compute_bollinger,
    "atr": compute_atr,
    "sma50": lambda df, params: compute_sma(df, 50),
    "sma200": lambda df, params: compute_sma(df, 200)
} 
