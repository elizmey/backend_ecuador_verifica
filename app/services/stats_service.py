from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.news import NewsArticle
from app.models.request import RequestStatus, Verdict, VerificationRequest
from app.models.source import Source, SourceReference
from app.models.user import User

_VERDICT_NON_NULL = tuple(v.value for v in Verdict)


def _naive_now() -> datetime:
    return datetime.utcnow()


def get_overview(db: Session) -> dict:
    total = db.scalar(select(func.count(VerificationRequest.id))) or 0

    status_rows = db.execute(
        select(
            VerificationRequest.status,
            func.count(VerificationRequest.id).label("cnt"),
        ).group_by(VerificationRequest.status)
    ).all()
    by_status = {s.value: c for s, c in status_rows}

    verdict_rows = db.execute(
        select(
            VerificationRequest.verdict,
            func.count(VerificationRequest.id).label("cnt"),
        )
        .where(VerificationRequest.verdict.is_not(None))
        .group_by(VerificationRequest.verdict)
    ).all()
    by_verdict = {v.value: c for v, c in verdict_rows}
    assigned = sum(by_verdict.values())
    by_verdict["sin_veredicto"] = max(total - assigned, 0)

    avg_confidence = db.scalar(
        select(func.avg(VerificationRequest.confidence))
    )
    avg_veracity = round(avg_confidence * 100, 1) if avg_confidence is not None else None

    now = _naive_now()
    requests_last_7 = (
        db.scalar(
            select(func.count(VerificationRequest.id)).where(
                VerificationRequest.created_at >= now - timedelta(days=7)
            )
        )
        or 0
    )
    requests_last_30 = (
        db.scalar(
            select(func.count(VerificationRequest.id)).where(
                VerificationRequest.created_at >= now - timedelta(days=30)
            )
        )
        or 0
    )

    return {
        "total_requests": total,
        "by_status": by_status,
        "by_verdict": by_verdict,
        "avg_confidence": avg_confidence,
        "avg_veracity_score": avg_veracity,
        "requests_last_7_days": requests_last_7,
        "requests_last_30_days": requests_last_30,
        "users_count": db.scalar(select(func.count(User.id))) or 0,
        "articles_count": db.scalar(select(func.count(NewsArticle.id))) or 0,
        "sources_count": db.scalar(select(func.count(Source.id))) or 0,
    }


def get_trends(db: Session, days: int = 30) -> list[dict]:
    cutoff = _naive_now() - timedelta(days=days)
    rows = db.execute(
        select(
            func.date(VerificationRequest.created_at).label("day"),
            func.count(VerificationRequest.id).label("cnt"),
        )
        .where(VerificationRequest.created_at >= cutoff)
        .group_by(func.date(VerificationRequest.created_at))
        .order_by(func.date(VerificationRequest.created_at))
    ).all()
    return [{"date": str(day), "count": cnt} for day, cnt in rows]


def get_top_sources(db: Session, limit: int = 10) -> list[dict]:
    rows = db.execute(
        select(
            Source.name,
            Source.domain,
            func.count(SourceReference.id).label("refs"),
        )
        .join(SourceReference, SourceReference.source_id == Source.id)
        .group_by(Source.id)
        .order_by(func.count(SourceReference.id).desc())
        .limit(limit)
    ).all()
    return [{"name": name, "domain": domain, "references": refs} for name, domain, refs in rows]


def get_pending_count(db: Session) -> int:
    return (
        db.scalar(
            select(func.count(VerificationRequest.id)).where(
                VerificationRequest.status == RequestStatus.pending
            )
        )
        or 0
    )
