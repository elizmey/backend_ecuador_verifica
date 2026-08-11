from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import list_users

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get("", response_model=list[UserRead], summary="Listar usuarios (admin)")
def list_all_users(
    db: Session = Depends(get_db),
    _: AdminUser = None,
    role: UserRole | None = Query(default=None),
) -> list[User]:
    return list_users(db, role=role)


@router.get("/{user_id}", response_model=UserRead, summary="Detalle de usuario (admin)")
def get_user_detail(
    db: Session = Depends(get_db),
    _: AdminUser = None,
    user_id: int = 0,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


@router.patch("/{user_id}", response_model=UserRead, summary="Actualizar usuario (admin)")
def update_user(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: AdminUser = None,
    user_id: int = 0,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "email" in data and data["email"]:
        data["email"] = data["email"].lower()
        existing = db.query(User).filter(User.email == data["email"], User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Correo en uso")
    if "password" in data and data["password"]:
        data["hashed_password"] = hash_password(data.pop("password"))

    for field, value in data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desactivar usuario (admin)")
def deactivate_user(
    db: Session = Depends(get_db),
    _: AdminUser = None,
    user_id: int = 0,
) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    user.is_active = False
    db.commit()
