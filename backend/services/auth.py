import functools

from flask import session

from services.exceptions import UserNotAuthenticatedException


def login_required(view):

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('user_id') is None:
            raise UserNotAuthenticatedException()
        return view(**kwargs)

    return wrapped_view