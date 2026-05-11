import functools

from flask import session

from models import User
from services import UserService, UserNotAuthenticatedException


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            raise UserNotAuthenticatedException()
        return view(**kwargs)

    return wrapped_view


def get_session_user() -> User:
    user_id: int | None = session.get("user_id")
    if user_id is None:
        raise UserNotAuthenticatedException()

    return UserService().get_user_by_id(user_id)
