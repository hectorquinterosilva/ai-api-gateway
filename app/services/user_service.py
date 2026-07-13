from app.exceptions.user_exceptions import (
    EmailAlreadyExistsException,
    UserNotFoundException
)
from sqlalchemy.orm import Session

from app.models.user import User


def create_user(
    db: Session,
    name: str,
    email: str
) -> User:

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:

        raise EmailAlreadyExistsException()

    user = User(
        name=name,
        email=email
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user


def get_users(
    db: Session
):

    return db.query(User).all()


def get_user_by_id(
    db: Session,
    user_id: int
):

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        raise UserNotFoundException()

    return user

def update_user(
    db: Session,
    user_id: int,
    name: str,
    email: str
):

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        raise UserNotFoundException()

    existing_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.id != user_id
        )
        .first()
    )

    if existing_user:

        raise EmailAlreadyExistsException()

    user.name = name
    user.email = email

    db.commit()

    db.refresh(user)

    return user

def delete_user(
    db: Session,
    user_id: int
):

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        raise UserNotFoundException()

    db.delete(user)

    db.commit()

    return {
        "message": "User deleted successfully"
    }
