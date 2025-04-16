from core.indicators.rsi import compute_rsi
from core.indicators.macd import compute_macd
from core.indicators.bollinger import compute_bollinger
from core.indicators.atr import compute_atr
from core.indicators.sma import compute_sma
from core.indicators.ema import compute_ema
from core.indicators.adx import compute_adx
from core.indicators.cci import compute_cci
from core.indicators.williams import compute_williams

registry = {
    # Momentum
    "rsi": compute_rsi,
    "macd": compute_macd,
    "williams": compute_williams,

    # Volatility
    "bollinger": compute_bollinger,
    "atr": compute_atr,

    # Trend
    "adx": compute_adx,
    "cci": compute_cci,

    # EMA aliases - wrap as dict for parameter safety
    "ema5": lambda df, params: compute_ema(df, {"period": 5}),
    "ema10": lambda df, params: compute_ema(df, {"period": 10}),
    "ema20": lambda df, params: compute_ema(df, {"period": 20}),
    "ema50": lambda df, params: compute_ema(df, {"period": 50}),
    "ema200": lambda df, params: compute_ema(df, {"period": 200}),

    # SMA aliases
    "sma5": lambda df, params: compute_sma(df, {"period": 5}),
    "sma10": lambda df, params: compute_sma(df, {"period": 10}),
    "sma50": lambda df, params: compute_sma(df, {"period": 50}),
    "sma200": lambda df, params: compute_sma(df, {"period": 200}),
}
