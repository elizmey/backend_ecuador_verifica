from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.news import NewsArticle
from app.models.request import RequestMediaType, VerificationRequest
from app.models.user import User, UserRole
from app.services.request_service import dispatch_processing


def create_article(
    db: Session,
    owner: User,
    title: str,
    content: str,
    author: str | None = None,
    url: str | None = None,
    medium: str | None = None,
    published_at: datetime | None = None,
) -> NewsArticle:
    article = NewsArticle(
        title=title.strip(),
        content=content.strip(),
        author=author,
        url=url,
        medium=medium,
        published_at=published_at,
        user_id=owner.id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_article(db: Session, article_id: int) -> NewsArticle | None:
    return db.scalar(
        select(NewsArticle)
        .options(selectinload(NewsArticle.verifications))
        .where(NewsArticle.id == article_id)
    )


def list_articles(
    db: Session, limit: int = 50, offset: int = 0
) -> list[NewsArticle]:
    stmt = (
        select(NewsArticle)
        .options(selectinload(NewsArticle.verifications))
        .order_by(NewsArticle.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt))


def delete_article(db: Session, article_id: int, user: User) -> None:
    article = get_article(db, article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Noticia no encontrada"
        )
    if article.user_id != user.id and user.role == UserRole.user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes eliminar esta noticia",
        )
    db.delete(article)
    db.commit()


def process_article(db: Session, article_id: int, user: User) -> VerificationRequest:
    article = get_article(db, article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Noticia no encontrada"
        )

    req = VerificationRequest(
        user_id=user.id,
        claim=article.content or article.title,
        media_type=RequestMediaType.text,
        images=[],
        article_id=article.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    dispatch_processing(req.id)
    return req
