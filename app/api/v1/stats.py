from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import VerifierOrAdmin
from app.schemas.stats import StatsOverview, TopSource, TrendPoint
from app.services.stats_service import get_overview, get_top_sources, get_trends

router = APIRouter(prefix="/stats", tags=["Estadísticas"])


@router.get("/overview", response_model=StatsOverview, summary="Resumen general de la plataforma")
def overview(
    db: Session = Depends(get_db),
    _: VerifierOrAdmin = None,
) -> dict:
    return get_overview(db)


@router.get("/trends", response_model=list[TrendPoint], summary="Tendencia de solicitudes por día")
def trends(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: VerifierOrAdmin = None,
) -> list[TrendPoint]:
    return get_trends(db, days=days)


@router.get(
    "/top-sources",
    response_model=list[TopSource],
    summary="Fuentes más referenciadas en los análisis",
)
def top_sources(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: VerifierOrAdmin = None,
) -> list[TopSource]:
    return get_top_sources(db, limit=limit)
