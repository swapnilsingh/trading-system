from .rsi import compute_rsi
from .macd import compute_macd
from .bollinger import compute_bollinger
from .sma import compute_sma
from .ema import compute_ema
from .atr import compute_atr
from .adx import compute_adx
from .cci import compute_cci
from .williams import compute_williams

registry = {
    # Core indicators
    "rsi": compute_rsi,
    "macd": compute_macd,
    "bollinger": compute_bollinger,
    "atr": compute_atr,
    "adx": compute_adx,
    "cci": compute_cci,
    "williams": compute_williams,

    # SMA aliases
    "sma5": lambda df, params: compute_sma(df, 5),
    "sma10": lambda df, params: compute_sma(df, 10),
    "sma50": lambda df, params: compute_sma(df, 50),
    "sma200": lambda df, params: compute_sma(df, 200),

    # EMA aliases
    "ema5": lambda df, params: compute_ema(df, 5),
    "ema10": lambda df, params: compute_ema(df, 10),
    "ema20": lambda df, params: compute_ema(df, 20),
    "ema50": lambda df, params: compute_ema(df, 50),
    "ema200": lambda df, params: compute_ema(df, 200),

    # Fallback dynamic SMA/EMA with parameterized windows
    "sma": lambda df, params: compute_sma(df, params.get("window", 14)),
    "ema": lambda df, params: compute_ema(df, params.get("window", 14)),
}
