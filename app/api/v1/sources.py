from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser, CurrentUser
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceRead, SourceUpdate
from app.services.source_verification import match_sources_for_text

router = APIRouter(prefix="/sources", tags=["Fuentes"])


@router.get("", response_model=list[SourceRead], summary="Listar fuentes registradas")
def list_sources(
    verified_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> list[Source]:
    stmt = select(Source).order_by(Source.name)
    if verified_only:
        stmt = stmt.where(Source.is_verified.is_(True))
    return list(db.scalars(stmt))


@router.get(
    "/{source_id}",
    response_model=SourceRead,
    summary="Detalle de una fuente",
)
def source_detail(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fuente no encontrada"
        )
    return source


@router.post(
    "",
    response_model=SourceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una fuente confiable (admin)",
)
def create_source(
    payload: SourceCreate,
    db: Session = Depends(get_db),
    admin: AdminUser = None,
) -> Source:
    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch(
    "/{source_id}",
    response_model=SourceRead,
    summary="Actualizar una fuente (admin)",
)
def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = None,
) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fuente no encontrada"
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete(
    "/{source_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una fuente (admin)"
)
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = None,
) -> None:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Fuente no encontrada"
        )
    db.delete(source)
    db.commit()


@router.get(
    "/match/text",
    response_model=list[dict],
    summary="Cruzar un texto contra las fuentes confiables (sin persistir)",
)
def match_text(
    text: str = Query(..., min_length=3, max_length=10000),
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> list[dict]:
    sources = list(db.scalars(select(Source).where(Source.is_verified.is_(True))))
    matches = match_sources_for_text(sources, text)
    return [
        {
            "source_id": m.source.id,
            "name": m.source.name,
            "domain": m.source.domain,
            "match_type": m.match_type,
            "similarity": m.similarity,
        }
        for m in matches
    ]
