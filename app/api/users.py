from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.schemas.user import UserCreate
from app.schemas.user import UserResponse

from app.services.user_service import (
    create_user,
    get_users,
    get_user_by_id,
    update_user,
    delete_user
)

from app.exceptions.user_exceptions import (
    EmailAlreadyExistsException,
    UserNotFoundException
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post(
    "",
    response_model=UserResponse
)
def create_user_endpoint(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    try:

        return create_user(
            db,
            user.name,
            user.email
        )

    except EmailAlreadyExistsException:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )


@router.get(
    "",
    response_model=list[UserResponse]
)
def get_users_endpoint(
    db: Session = Depends(get_db)
):

    return get_users(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user_by_id_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):

    try:

        return get_user_by_id(
            db,
            user_id
        )

    except UserNotFoundException:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
@router.put(
    "/{user_id}",
    response_model=UserResponse
)
def update_user_endpoint(
    user_id: int,
    user: UserCreate,
    db: Session = Depends(get_db)
):

    try:

        return update_user(
            db,
            user_id,
            user.name,
            user.email
        )

    except UserNotFoundException:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    except EmailAlreadyExistsException:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )


@router.delete(
    "/{user_id}"
)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):

    try:

        return delete_user(
            db,
            user_id
        )

    except UserNotFoundException:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )