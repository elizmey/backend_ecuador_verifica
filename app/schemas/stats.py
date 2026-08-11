from pydantic import BaseModel


class StatsOverview(BaseModel):
    total_requests: int
    by_status: dict[str, int]
    by_verdict: dict[str, int]
    avg_confidence: float | None
    avg_veracity_score: float | None
    requests_last_7_days: int
    requests_last_30_days: int
    users_count: int
    articles_count: int
    sources_count: int


class TrendPoint(BaseModel):
    date: str
    count: int


class TopSource(BaseModel):
    name: str
    domain: str
    references: int
