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