import sqlite3
import logging

from db import get_db
from models import User
from daos.exceptions import ServiceInternalException

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class UserDAO(object):

    def save_user(self, user:User) -> None:
        try:
            pass_hash = user.generate_password_hash()
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (email, password) VALUES (?, ?)",
                    (user.email, pass_hash),
                )
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error saving user")
