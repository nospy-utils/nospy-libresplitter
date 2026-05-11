import sqlite3
import logging

from database import get_db
from models import User
from daos.exceptions import ServiceInternalException, ServiceUnavailableException

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class UserDAO(object):

    def find_by_id(self, user_id: int):
        try:
            with get_db() as conn:
                return conn.execute(
                    "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
                ).fetchone()
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error looking up user")

    def find_by_email(self, email: str):
        try:
            with get_db() as conn:
                return conn.execute(
                    "SELECT id, name, email, password FROM users WHERE email = ?",
                    (email,),
                ).fetchone()
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error looking up user")

    def save_user(self, user: User) -> None:
        try:
            pass_hash = user.generate_password_hash()
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (user.name, user.email, pass_hash),
                )
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error saving user")
