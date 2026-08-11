from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(
    db: Session, email: str, full_name: str, password: str, role: UserRole = UserRole.user
) -> User:
    user = User(
        email=email.lower(),
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, role: UserRole | None = None) -> list[User]:
    stmt = select(User).order_by(User.created_at.desc())
    if role is not None:
        stmt = stmt.where(User.role == role)
    return list(db.scalars(stmt))
