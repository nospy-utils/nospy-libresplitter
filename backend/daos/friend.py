import sqlite3
import logging

from database import get_db
from models import User
from daos.exceptions import ServiceInternalException, ServiceUnavailableException

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class FriendDAO(object):

    def add_friend(self, user: User, friend: User) -> None:
        # Normalize ordering so (a,b) and (b,a) map to the same row.
        a, b = (user.user_id, friend.user_id) if user.user_id < friend.user_id else (friend.user_id, user.user_id)
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO friends (friend_1, friend_2) VALUES (?, ?)", (a, b)
                )
        except sqlite3.IntegrityError:
            from services.exceptions import FriendAlreadyExistsException
            raise FriendAlreadyExistsException()
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error saving friend relationship")

    def list_friends(self, user: User) -> list:
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT u.id, u.name, u.email
                    FROM friends f
                    JOIN users u ON (f.friend_1 = u.id OR f.friend_2 = u.id)
                    WHERE (f.friend_1 = ? OR f.friend_2 = ?) AND u.id != ?
                    ORDER BY u.name
                    """,
                    (user.user_id, user.user_id, user.user_id),
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error listing friends")
