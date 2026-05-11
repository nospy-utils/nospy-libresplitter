import sqlite3
import logging

from database import get_db
from models import User
from daos.exceptions import ServiceInternalException, ServiceUnavailableException
from utils.pagination import Page

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class FriendDAO(object):

    def add_friend(self, user: User, friend: User) -> None:
        # Normalize ordering so (a,b) and (b,a) map to the same row.
        a, b = (
            (user.user_id, friend.user_id)
            if user.user_id < friend.user_id
            else (friend.user_id, user.user_id)
        )
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

    def get_recent_friends(self, user: User, page: Page) -> dict:
        offset = (page.current_page - 1) * page.page_size
        try:
            with get_db() as conn:
                total = conn.execute(
                    """
                    SELECT COUNT(*) AS cnt
                    FROM friends f
                    WHERE f.friend_1 = ? OR f.friend_2 = ?
                    """,
                    (user.user_id, user.user_id),
                ).fetchone()["cnt"]

                rows = conn.execute(
                    """
                    SELECT u.id, u.name
                    FROM
                        (
                            SELECT
                                CASE WHEN f.friend_1 = ? THEN f.friend_2 ELSE f.friend_1 END AS friend_id
                            FROM
                                friends f
                            WHERE
                                f.friend_1 = ? OR f.friend_2 = ?
                        ) AS f LEFT JOIN
                        (
                            SELECT 
                                CASE WHEN eu.from_user_id = ? THEN eu.to_user_id ELSE eu.from_user_id END AS friend_id,
                                MAX(ex.created_at) AS last_interaction
                              FROM expense_user eu INNER JOIN expenses ex 
                                  ON eu.expense_id = ex.id
                              WHERE eu.from_user_id = ?
                                 OR eu.to_user_id = ?
                              GROUP BY friend_id
                        ) AS t ON t.friend_id = f.friend_id
                        INNER JOIN users u on (u.id = f.friend_id)
                    ORDER BY t.last_interaction DESC
                    LIMIT ? OFFSET ?
                    """,
                    (
                        user.user_id,
                        user.user_id,
                        user.user_id,
                        user.user_id,
                        user.user_id,
                        user.user_id,
                        page.page_size,
                        offset,
                    ),
                ).fetchall()

                return {
                    "friends": [dict(r) for r in rows],
                    "total": total,
                    "page": page.current_page,
                    "page_size": page.page_size,
                    "has_next": (offset + page.page_size) < total,
                }
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error fetching recent friends")

    def are_friends(self, user: User, other_user: User) -> bool:
        try:
            with get_db() as conn:
                row = conn.execute(
                    """
                    SELECT 1
                    FROM friends f
                    JOIN users u ON (f.friend_1 = u.id OR f.friend_2 = u.id)
                    WHERE
                        ((f.friend_1 = ? AND f.friend_2 = ?) OR
                        (f.friend_1 = ? AND f.friend_2 = ?)) AND
                        u.id != ?
                    ORDER BY u.name
                    """,
                    (
                        user.user_id,
                        other_user.user_id,
                        other_user.user_id,
                        user.user_id,
                        other_user.user_id,
                    ),
                ).fetchone()
                return row is not None
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error checking friend relationship")
