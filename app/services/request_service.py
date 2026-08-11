import threading

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.request import (
    RequestMediaType,
    RequestStatus,
    VerificationRequest,
)
from app.models.user import User, UserRole

settings = get_settings()


def create_request(
    db: Session,
    owner: User,
    claim: str,
    media_type: RequestMediaType,
    images: list[str] | None = None,
) -> VerificationRequest:
    req = VerificationRequest(
        user_id=owner.id,
        claim=claim.strip(),
        media_type=media_type,
        images=images or [],
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_request(db: Session, request_id: int) -> VerificationRequest | None:
    return db.scalar(
        select(VerificationRequest)
        .options(selectinload(VerificationRequest.analyses))
        .where(VerificationRequest.id == request_id)
    )


def get_owned_request(db: Session, request_id: int, user: User) -> VerificationRequest:
    req = get_request(db, request_id)
    if req is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud no encontrada")
    if req.user_id != user.id and user.role == UserRole.user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes acceder a esta solicitud")
    return req


def list_requests(
    db: Session,
    user: User,
    status_filter: RequestStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[VerificationRequest]:
    stmt = (
        select(VerificationRequest)
        .options(selectinload(VerificationRequest.analyses))
        .order_by(VerificationRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if user.role == UserRole.user:
        stmt = stmt.where(VerificationRequest.user_id == user.id)
    if status_filter is not None:
        stmt = stmt.where(VerificationRequest.status == status_filter)
    return list(db.scalars(stmt))


def delete_request(db: Session, request_id: int, user: User) -> None:
    req = get_owned_request(db, request_id, user)
    db.delete(req)
    db.commit()


def dispatch_processing(request_id: int) -> None:
    """Envía la solicitud al backend de tareas configurado (celery o inline)."""
    if settings.WORKER_BACKEND == "celery":
        from app.workers.tasks import process_request_task

        process_request_task.delay(request_id)
        return

    from app.core.database import SessionLocal
    from app.services.ai.pipeline import run_request_pipeline

    def _run() -> None:
        db = SessionLocal()
        try:
            run_request_pipeline(db, request_id)
        except Exception:  # noqa: BLE001 - el error queda registrado en la solicitud
            pass
        finally:
            db.close()

    threading.Thread(target=_run, daemon=True).start()
