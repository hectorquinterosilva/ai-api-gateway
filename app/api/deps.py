from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.security import hash_api_key
from app.db.session import get_db
from app.models.user import User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user(
    api_key: str | None = Depends(api_key_header),
    db: Session = Depends(get_db),
) -> User:
    """
    Resuelve el User a partir del header X-API-Key.
    Devuelve 401 si falta, no existe o el usuario está inactivo.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_hash = hash_api_key(api_key)
    user = (
        db.query(User)
        .filter(User.api_key_hash == key_hash)
        .first()
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return user
