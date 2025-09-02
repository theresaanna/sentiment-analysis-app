from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Analysis:
    id: str
    post_url: str
    status: str  # pending, processing, completed, failed
    created_at: str
    updated_at: str
    results: Optional[Dict[Any, Any]] = None
    error: Optional[str] = None

@dataclass
class SentimentResult:
    total_comments: int
    sentiment_breakdown: Dict[str, int]  # positive, negative, neutral counts
    average_sentiment: float
    top_keywords: list
    comments_sample: list