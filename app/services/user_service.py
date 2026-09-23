from sqlalchemy.orm import Session

from app.core.security import generate_api_key, hash_api_key
from app.exceptions.user_exceptions import (
    EmailAlreadyExistsException,
    UserNotFoundException,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


# ----------------------------
# Helpers internos
# ----------------------------
def _get_user_or_raise(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException()
    return user


# ----------------------------
# CRUD
# ----------------------------
def create_user(db: Session, payload: UserCreate) -> tuple[User, str]:
    """
    Crea un usuario y le emite su primera API key.
    Devuelve (user, plain_api_key). La key en claro solo se ve aquí.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise EmailAlreadyExistsException()

    plain_key = generate_api_key()

    user = User(
        name=payload.name,
        email=payload.email,
        role=payload.role,
        tenant_id=payload.tenant_id,
        api_key_hash=hash_api_key(plain_key),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, plain_key


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    include_inactive: bool = False,
) -> tuple[list[User], int]:
    query = db.query(User)

    if not include_inactive:
        query = query.filter(User.is_active.is_(True))

    total = query.count()
    items = query.order_by(User.id).offset(skip).limit(limit).all()
    return items, total


def get_user_by_id(db: Session, user_id: int) -> User:
    return _get_user_or_raise(db, user_id)


def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
    user = _get_user_or_raise(db, user_id)

    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"] != user.email:
        existing = (
            db.query(User)
            .filter(User.email == data["email"], User.id != user_id)
            .first()
        )
        if existing:
            raise EmailAlreadyExistsException()

    for field, value in data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> User:
    """Soft delete: marca is_active=False, no borra la fila."""
    user = _get_user_or_raise(db, user_id)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


def reactivate_user(db: Session, user_id: int) -> User:
    user = _get_user_or_raise(db, user_id)
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


# ----------------------------
# API keys
# ----------------------------
def issue_api_key(db: Session, user_id: int) -> tuple[User, str]:
    """Rota la API key. Devuelve (user, nueva_key_en_claro)."""
    user = _get_user_or_raise(db, user_id)
    plain_key = generate_api_key()
    user.api_key_hash = hash_api_key(plain_key)
    db.commit()
    db.refresh(user)
    return user, plain_key


def revoke_api_key(db: Session, user_id: int) -> User:
    user = _get_user_or_raise(db, user_id)
    user.api_key_hash = None
    db.commit()
    db.refresh(user)
    return user
