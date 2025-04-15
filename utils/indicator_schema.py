# utils/indicator_schema.py
from typing import Optional, Dict, Any
from pydantic import BaseModel

class IndicatorRequestParams(BaseModel):
    start_time: str
    end_time: str
    params: Optional[Dict[str, Any]] = None

class IndicatorAPIRequest(BaseModel):
    symbol: str
    interval: str  # e.g., '1min', '5min'
    indicators: Dict[str, IndicatorRequestParams]
