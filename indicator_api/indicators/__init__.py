from .rsi import compute_rsi
from .macd import compute_macd
from .bollinger import compute_bollinger
from .sma import compute_sma

registry = {
    "rsi": compute_rsi,
    "macd": compute_macd,
    "bollinger": compute_bollinger,
    "sma5": lambda df, params: compute_sma(df, 5),
    "sma10": lambda df, params: compute_sma(df, 10)
}
