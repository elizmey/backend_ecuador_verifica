from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.news import NewsArticle
from app.schemas.news import (
    NewsArticleCreate,
    NewsArticleDetail,
    NewsArticleList,
    NewsArticleRead,
)
from app.services.news_service import (
    create_article,
    delete_article,
    get_article,
    list_articles,
    process_article,
)

router = APIRouter(prefix="/news", tags=["Noticias"])


@router.post(
    "",
    response_model=NewsArticleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una noticia para su análisis",
)
def create_news_article(
    payload: NewsArticleCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> NewsArticle:
    return create_article(
        db,
        current_user,
        title=payload.title,
        content=payload.content,
        author=payload.author,
        url=payload.url,
        medium=payload.medium,
        published_at=payload.published_at,
    )


@router.get("", response_model=NewsArticleList, summary="Listar noticias")
def list_news(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> NewsArticleList:
    items = list_articles(db, limit=limit, offset=offset)
    total = db.scalar(select(func.count(NewsArticle.id))) or 0
    return NewsArticleList(items=items, total=total)


@router.get("/{article_id}", response_model=NewsArticleDetail, summary="Detalle de una noticia")
def news_detail(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> NewsArticle:
    article = get_article(db, article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Noticia no encontrada"
        )
    return article


@router.delete(
    "/{article_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una noticia"
)
def remove_news(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> None:
    delete_article(db, article_id, current_user)


@router.post(
    "/{article_id}/process",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Analizar la noticia creando una solicitud vinculada",
)
def process_news_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
):
    req = process_article(db, article_id, current_user)
    return {"request_id": req.id, "status": req.status.value}
