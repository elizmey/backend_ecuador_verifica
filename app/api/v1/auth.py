from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, get_current_user
from app.core.security import create_access_token, verify_password
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.user_service import create_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
def register(
    payload: RegisterRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    if get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )
    user = create_user(
        db, email=payload.email, full_name=payload.full_name, password=payload.password
    )
    token = create_access_token(subject=user.id, role=user.role.value)
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión (OAuth2 password flow)",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = get_user_by_email(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Usuario desactivado"
        )
    token = create_access_token(subject=user.id, role=user.role.value)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Obtener el usuario autenticado",
)
def me(current_user: CurrentUser) -> UserRead:
    return current_user
