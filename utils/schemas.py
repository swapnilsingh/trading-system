# utils/schemas.py
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ValidationError, Field, conlist

TICK_SCHEMA = [
    "symbol", "price", "quantity", "trade_time"
]

OHLCV_SCHEMA = [
    "symbol", "open", "high", "low", "close", "volume", "start_time", "end_time"
]

TRADE_LOG_SCHEMA = [
    "symbol", "action", "price", "quantity", "timestamp", "strategy", "agent_id"
]

VOTE_SCHEMA = [
    "symbol", "agent_id", "timestamp", "vote"
]

EQUITY_CURVE_SCHEMA = [
    "timestamp", "capital", "unrealized_pnl", "realized_pnl"
]

INDICATOR_SCHEMA = [
    "symbol", "timestamp", "rsi", "macd", "macd_signal", "bollinger_upper", "bollinger_lower", "bollinger_middle", "atr"
]

class TickModel(BaseModel):
    symbol: str
    price: float
    quantity: float
    trade_time: str

class OHLCVModel(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    start_time: str
    end_time: str

class TradeLogModel(BaseModel):
    symbol: str
    action: str  # 'buy' or 'sell'
    price: float
    quantity: float
    timestamp: str
    strategy: Optional[str] = Field(default="default")
    agent_id: Optional[str] = Field(default="anonymous")

class VoteModel(BaseModel):
    symbol: str
    agent_id: str
    timestamp: str
    vote: int  # -1, 0, 1

class EquityCurveModel(BaseModel):
    timestamp: str
    capital: float
    unrealized_pnl: float
    realized_pnl: float

class IndicatorModel(BaseModel):
    symbol: str
    timestamp: str
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    bollinger_middle: Optional[float] = None
    atr: Optional[float] = None

# API Request/Response Schemas
class SignalRequest(BaseModel):
    symbol: str
    timestamp: str
    indicators: Dict[str, Optional[float]]

class SignalResponse(BaseModel):
    symbol: str
    timestamp: str
    signal: int  # -1 sell, 0 hold, 1 buy
    reason: Optional[str] = None

class TradeExecutionRequest(BaseModel):
    symbol: str
    action: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: str
    strategy: Optional[str] = "default"
    agent_id: Optional[str] = "anonymous"

class TradeExecutionResponse(BaseModel):
    trade_id: str
    status: str  # 'success', 'failed'
    message: Optional[str] = None
    executed_price: Optional[float] = None
    timestamp: Optional[str] = None

# Model inference related schemas
class ModelInferenceRequest(BaseModel):
    model_name: str
    input_features: conlist(float, min_items=1)
    timestamp: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class ModelInferenceResponse(BaseModel):
    model_name: str
    output: float
    predicted_class: Optional[int] = None
    confidence: Optional[float] = None
    timestamp: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class AgentInput(BaseModel):
    symbol: str
    timestamp: str
    indicators: Dict[str, Optional[float]]
    meta: Optional[Dict[str, Any]] = None

class AgentOutput(BaseModel):
    symbol: str
    timestamp: str
    action: int
    confidence: Optional[float] = None
    agent_id: Optional[str] = None
    explanation: Optional[str] = None

class BatchModelInferenceRequest(BaseModel):
    model_name: str
    input_batch: List[conlist(float, min_items=1)]
    timestamps: Optional[List[str]] = None

SCHEMA_REGISTRY = {
    "tick": TickModel,
    "ohlcv": OHLCVModel,
    "trade_log": TradeLogModel,
    "vote": VoteModel,
    "equity": EquityCurveModel,
    "indicator": IndicatorModel,
    "signal_request": SignalRequest,
    "signal_response": SignalResponse,
    "trade_execution_request": TradeExecutionRequest,
    "trade_execution_response": TradeExecutionResponse,
    "model_inference_request": ModelInferenceRequest,
    "model_inference_response": ModelInferenceResponse,
    "agent_input": AgentInput,
    "agent_output": AgentOutput,
    "batch_model_inference_request": BatchModelInferenceRequest
}

def format_data_by_type(data: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
    model = SCHEMA_REGISTRY.get(schema_type)
    if not model:
        raise ValueError(f"Unknown schema type: {schema_type}")
    try:
        return model(**data).dict()
    except ValidationError as e:
        raise ValueError(f"Invalid {schema_type} data: {e}")

def format_tick_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return format_data_by_type(data, "tick")

def format_ohlcv_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return format_data_by_type(data, "ohlcv")

def format_trade_log(data: Dict[str, Any]) -> Dict[str, Any]:
    return format_data_by_type(data, "trade_log")

def format_vote(data: Dict[str, Any]) -> Dict[str, Any]:
    return format_data_by_type(data, "vote")

def format_equity_curve(data: Dict[str, Any]) -> Dict[str, Any]:
    return format_data_by_type(data, "equity")

def format_indicator_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return format_data_by_type(data, "indicator")
