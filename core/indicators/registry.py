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
    "rsi": {
        "func": compute_rsi,
        "category": "momentum",
        "description": "Relative Strength Index",
        "params": {}
    },
    "macd": {
        "func": compute_macd,
        "category": "momentum",
        "description": "Moving Average Convergence Divergence",
        "params": {}
    },
    "williams": {
        "func": compute_williams,
        "category": "momentum",
        "description": "Williams %R Oscillator",
        "params": {}
    },

    # Volatility
    "bollinger": {
        "func": compute_bollinger,
        "category": "volatility",
        "description": "Bollinger Bands",
        "params": {}
    },
    "atr": {
        "func": compute_atr,
        "category": "volatility",
        "description": "Average True Range",
        "params": {}
    },

    # Trend
    "adx": {
        "func": compute_adx,
        "category": "trend",
        "description": "Average Directional Index",
        "params": {}
    },
    "cci": {
        "func": compute_cci,
        "category": "trend",
        "description": "Commodity Channel Index",
        "params": {}
    },

    # EMA aliases
    "ema5": {
        "func": lambda df, params: compute_ema(df, {"window": 5}),
        "category": "trend",
        "description": "Exponential Moving Average (5)",
        "params": {"window": 5}
    },
    "ema10": {
        "func": lambda df, params: compute_ema(df, {"window": 10}),
        "category": "trend",
        "description": "Exponential Moving Average (10)",
        "params": {"window": 10}
    },
    "ema20": {
        "func": lambda df, params: compute_ema(df, {"window": 20}),
        "category": "trend",
        "description": "Exponential Moving Average (20)",
        "params": {"window": 20}
    },
    "ema50": {
        "func": lambda df, params: compute_ema(df, {"window": 50}),
        "category": "trend",
        "description": "Exponential Moving Average (50)",
        "params": {"window": 50}
    },
    "ema200": {
        "func": lambda df, params: compute_ema(df, {"window": 200}),
        "category": "trend",
        "description": "Exponential Moving Average (200)",
        "params": {"window": 200}
    },

    # SMA added
    "sma": {
        "func": compute_sma,
        "category": "trend",
        "description": "Simple Moving Average",
        "params": {"window": 20}  # Default SMA window
    },

    # SMA aliases
    "sma5": {
        "func": lambda df, params: compute_sma(df, {"window": 5}),
        "category": "trend",
        "description": "Simple Moving Average (5)",
        "params": {"window": 5}
    },
    "sma10": {
        "func": lambda df, params: compute_sma(df, {"window": 10}),
        "category": "trend",
        "description": "Simple Moving Average (10)",
        "params": {"window": 10}
    },
    "sma20": {
        "func": lambda df, params: compute_sma(df, {"window": 20}),
        "category": "trend",
        "description": "Simple Moving Average (20)",
        "params": {"window": 20}
    },
    "sma50": {
        "func": lambda df, params: compute_sma(df, {"window": 50}),
        "category": "trend",
        "description": "Simple Moving Average (50)",
        "params": {"window": 50}
    },
    "sma200": {
        "func": lambda df, params: compute_sma(df, {"window": 200}),
        "category": "trend",
        "description": "Simple Moving Average (200)",
        "params": {"window": 200}
    },
}
