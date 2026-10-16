from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


class LoginRequired(Exception):
    """Raised when a page needs a signed-in user; handled by redirecting to /login."""


def current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    user_id = request.session.get("user_id")
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise LoginRequired()
    return user


DB = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(current_user)]
