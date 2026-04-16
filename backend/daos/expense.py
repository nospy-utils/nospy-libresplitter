import sqlite3
import logging

from database import get_db
from models import User
from daos.exceptions import ServiceInternalException, ServiceUnavailableException

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class ExpenseDAO(object):

    def get_totals_by_currency(self, user: User) -> list:
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT
                      e.currency,
                      SUM(CASE WHEN eu.from_user_id = ? THEN eu.value ELSE -eu.value END) AS my_total
                    FROM expenses e
                    INNER JOIN expense_user eu ON e.id = eu.expense_id
                    WHERE eu.from_user_id = ? OR eu.to_user_id = ?
                    GROUP BY e.currency
                    """,
                    (user.user_id, user.user_id, user.user_id),
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error fetching expense totals")

    def get_totals_by_friend(self, user: User) -> list:
        """Returns how much the user owes/is owed per friend per currency."""
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT
                      CASE WHEN eu.from_user_id = ? THEN eu.to_user_id ELSE eu.from_user_id END AS friend_id,
                      u.name AS friend_name,
                      e.currency,
                      SUM(CASE WHEN eu.from_user_id = ? THEN eu.value ELSE -eu.value END) AS net_total
                    FROM expenses e
                    INNER JOIN expense_user eu ON e.id = eu.expense_id
                    INNER JOIN users u ON u.id = CASE WHEN eu.from_user_id = ? THEN eu.to_user_id ELSE eu.from_user_id END
                    WHERE eu.from_user_id = ? OR eu.to_user_id = ?
                    GROUP BY friend_id, e.currency
                    HAVING net_total != 0;
                    """,
                    (user.user_id, user.user_id, user.user_id, user.user_id, user.user_id),
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error fetching friend expense totals")

    def get_expenses_with_friend(self, user: User, friend_id: int) -> list:
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT
                      e.id,
                      CASE WHEN eu.from_user_id = ? THEN 'You' ELSE uf.name END AS from_user_name,
                      e.description,
                      e.currency,
                      e.value AS expense_total,
                      eu.value,
                      e.created_at
                    FROM expenses e
                    INNER JOIN expense_user eu ON e.id = eu.expense_id
                    INNER JOIN users uf ON eu.from_user_id = uf.id
                    WHERE
                        (eu.from_user_id = ? AND eu.to_user_id = ?) OR
                        (eu.from_user_id = ? AND eu.to_user_id = ?)
                    ORDER BY e.id DESC
                    """,
                    (user.user_id, user.user_id, friend_id, friend_id, user.user_id),
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error fetching expenses with friend")

    def get_settle_up_amount(self, user: User, friend_id: int) -> list:
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        t.friend_id,
                        u.name AS friend_name,
                        t.currency,
                        t.net_total
                    FROM (
                        SELECT
                            CASE WHEN eu.from_user_id = ? THEN eu.to_user_id ELSE eu.from_user_id END AS friend_id,
                            e.currency,
                            SUM(CASE WHEN eu.from_user_id = ? THEN eu.value ELSE -eu.value END) AS net_total
                        FROM expenses e
                        INNER JOIN expense_user eu ON e.id = eu.expense_id
                        WHERE eu.from_user_id = ? OR eu.to_user_id = ?
                        GROUP BY friend_id, e.currency
                    ) AS t
                    INNER JOIN users u ON t.friend_id = u.id
                    WHERE t.friend_id = ? AND t.net_total != 0
                    """,
                    (user.user_id, user.user_id, user.user_id, user.user_id, friend_id),
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error fetching settle up amount")

    def create_settle_up(self, user: User, friend: User, currency: str, value: float, reverse: bool) -> None:
        """Insert an expense + expense_user row representing a settle-up payment.

        reverse=False → current user paid the friend  (from_user_id=user, to_user_id=friend)
        reverse=True  → friend paid the current user  (from_user_id=friend, to_user_id=user)
        """
        if reverse:
            from_user_id = friend.user_id
            to_user_id = user.user_id
        else:
            from_user_id = user.user_id
            to_user_id = friend.user_id

        try:
            with get_db() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO expenses (user_created, currency, value, description)
                    VALUES (?, ?, ?, 'Settled up')
                    """,
                    (user.user_id, currency, value),
                )
                expense_id = cursor.lastrowid
                conn.execute(
                    """
                    INSERT INTO expense_user (expense_id, from_user_id, to_user_id, value)
                    VALUES (?, ?, ?, ?)
                    """,
                    (expense_id, from_user_id, to_user_id, value),
                )
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error recording settle up")

    def get_activity(self, user: User) -> list:
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT
                      e.id,
                      uf.name AS from_user_name,
                      (eu.from_user_id = ?) AS is_it_me,
                      e.description,
                      e.currency,
                      eu.value,
                      e.created_at
                    FROM expenses e
                    INNER JOIN expense_user eu ON e.id = eu.expense_id
                    INNER JOIN users uf ON eu.from_user_id = uf.id
                    WHERE eu.from_user_id = ? OR eu.to_user_id = ?
                    ORDER BY e.id DESC
                    """,
                    (user.user_id, user.user_id, user.user_id),
                ).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error fetching activity")
