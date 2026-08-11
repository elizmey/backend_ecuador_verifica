from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, VerifierOrAdmin
from app.models.request import RequestMediaType, RequestStatus, VerificationRequest
from app.schemas.request import (
    VerificationRequestCreate,
    VerificationRequestDetail,
    VerificationRequestRead,
    VerdictUpdate,
)
from app.services.request_service import (
    create_request,
    delete_request,
    dispatch_processing,
    get_owned_request,
    list_requests,
)
from app.services.storage import save_upload

router = APIRouter(prefix="/requests", tags=["Solicitudes de verificación"])


@router.post(
    "",
    response_model=VerificationRequestRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una solicitud de verificación",
)
async def create_verification_request(
    claim: str = Form(default="", max_length=10000),
    images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> VerificationRequest:
    saved_paths: list[str] = []
    if images:
        for image in images:
            saved_paths.append(await save_upload(image))

    if not claim.strip() and not saved_paths:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debes proporcionar un texto de afirmación o al menos una imagen",
        )

    if saved_paths and claim.strip():
        media_type = RequestMediaType.mixed
    elif saved_paths:
        media_type = RequestMediaType.image
    else:
        media_type = RequestMediaType.text

    return create_request(db, current_user, claim, media_type, saved_paths)


@router.get(
    "",
    response_model=list[VerificationRequestRead],
    summary="Listar solicitudes (las propias; todas para verifier/admin)",
)
def list_my_requests(
    status_filter: RequestStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> list[VerificationRequest]:
    return list_requests(db, current_user, status_filter=status_filter, limit=limit, offset=offset)


@router.get(
    "/{request_id}",
    response_model=VerificationRequestDetail,
    summary="Detalle de una solicitud con sus análisis",
)
def request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> VerificationRequest:
    return get_owned_request(db, request_id, current_user)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una solicitud")
def remove_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> None:
    delete_request(db, request_id, current_user)


@router.post(
    "/{request_id}/process",
    response_model=VerificationRequestRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Procesar la solicitud con el pipeline de IA (NLP + Vision + LLM)",
)
def process_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> VerificationRequest:
    req = get_owned_request(db, request_id, current_user)
    if req.status in (RequestStatus.processing, RequestStatus.completed):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La solicitud ya fue procesada o está en proceso",
        )
    dispatch_processing(request_id)
    req = get_owned_request(db, request_id, current_user)
    return req


@router.post(
    "/{request_id}/verdict",
    response_model=VerificationRequestRead,
    summary="Fijar veredicto final de una solicitud (verifier/admin)",
)
def set_verdict(
    request_id: int,
    payload: VerdictUpdate,
    db: Session = Depends(get_db),
    current_user: VerifierOrAdmin = None,
) -> VerificationRequest:
    req = get_owned_request(db, request_id, current_user)
    req.verdict = payload.verdict
    req.summary = payload.summary
    req.confidence = payload.confidence
    db.commit()
    db.refresh(req)
    return req
