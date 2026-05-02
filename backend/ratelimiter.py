import os
from flask import session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter:Limiter|None = None

def init_limiter(app) -> Limiter:
    global limiter

    if limiter is None:
        app.config['RATELIMIT_HEADERS_ENABLED'] = True
        app.config['RATELIMIT_DEFAULTS_PER_METHOD'] = True

        limiter = Limiter(
            get_rate_limiter_key,
            app=app,
            default_limits=["10/second"],
            storage_uri=os.environ.get("APP_RL_STORAGE_URI", "memcached://localhost:11211"),
        )

    return limiter

def get_rate_limiter_key() -> str:
    user_id: int | None = session.get('user_id')
    return user_id if user_id else get_remote_address()