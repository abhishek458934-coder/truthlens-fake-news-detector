from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VerifyRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None

class CheckResponse(BaseModel):
    id: int
    input_text: str
    score: int
    verdict: str
    reasons: list[str]
    official_source: str
    summary: str
    entities: list[str]
    ml_confidence: Optional[float]
    created_at: str
    cache_hit: bool = False

class StatsResponse(BaseModel):
    total: int
    likely_fake: int
    unverified: int
    verified: int
    avg_score: float
    most_recent_date: Optional[str]
