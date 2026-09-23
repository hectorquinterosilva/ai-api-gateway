from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.exceptions.user_exceptions import (
    EmailAlreadyExistsException,
    UserNotFoundException,
)
from app.models.user import User
from app.schemas.user import (
    ApiKeyResponse,
    UserCreate,
    UserCreateResponse,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================
# Público: registro
# ============================================================
@router.post(
    "",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        user, plain_key = user_service.create_user(db, payload)
    except EmailAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    base = UserResponse.model_validate(user).model_dump()
    return UserCreateResponse(**base, api_key=plain_key)


# ============================================================
# Protegido: a partir de aquí todo requiere X-API-Key
# ============================================================
@router.get("/me", response_model=UserResponse)
def get_me_endpoint(
    current: User = Depends(get_current_user),
):
    return current


@router.get("", response_model=UserListResponse)
def get_users_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = user_service.get_users(
        db,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
    )
    return UserListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return user_service.get_user_by_id(db, user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return user_service.update_user(db, user_id, payload)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except EmailAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return user_service.delete_user(db, user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/{user_id}/reactivate", response_model=UserResponse)
def reactivate_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return user_service.reactivate_user(db, user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


# ============================================================
# API keys
# ============================================================
@router.post("/{user_id}/api-key", response_model=ApiKeyResponse)
def rotate_api_key_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if current.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only rotate your own API key",
        )
    try:
        user, plain_key = user_service.issue_api_key(db, user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return ApiKeyResponse(user_id=user.id, api_key=plain_key)


@router.delete("/{user_id}/api-key", response_model=UserResponse)
def revoke_api_key_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if current.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only revoke your own API key",
        )
    try:
        return user_service.revoke_api_key(db, user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
