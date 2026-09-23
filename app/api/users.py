from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.exceptions.user_exceptions import (
    EmailAlreadyExistsException,
    UserNotFoundException,
)
from app.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


# ----------------------------
# Crear usuario
# ----------------------------
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_endpoint(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        return user_service.create_user(db, payload)
    except EmailAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


# ----------------------------
# Listar usuarios (paginado)
# ----------------------------
@router.get("", response_model=UserListResponse)
def get_users_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_inactive: bool = Query(False),
    db: Session = Depends(get_db),
):
    items, total = user_service.get_users(
        db,
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
    )
    return UserListResponse(items=items, total=total, skip=skip, limit=limit)


# ----------------------------
# Obtener uno
# ----------------------------
@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        return user_service.get_user_by_id(db, user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


# ----------------------------
# Actualizar (parcial)
# ----------------------------
@router.patch("/{user_id}", response_model=UserResponse)
def update_user_endpoint(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
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


# ----------------------------
# Soft delete
# ----------------------------
@router.delete("/{user_id}", response_model=UserResponse)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        return user_service.delete_user(db, user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


# ----------------------------
# Reactivar
# ----------------------------
@router.post("/{user_id}/reactivate", response_model=UserResponse)
def reactivate_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        return user_service.reactivate_user(db, user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
