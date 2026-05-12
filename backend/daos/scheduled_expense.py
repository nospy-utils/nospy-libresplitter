import sqlite3
import logging

from database import get_db
from models import User
from daos.exceptions import ServiceInternalException, ServiceUnavailableException

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class ScheduledExpenseDAO(object):

    def create_scheduled_expense(
        self,
        user: User,
        description: str,
        currency: str,
        value: float,
        participants: list,
        sched_day: int,
        sched_end: str = None,
    ) -> None:
        try:
            with get_db() as conn:
                cursor = conn.execute(
                    "INSERT INTO scheduled_expenses "
                    "(user_created, currency, value, description, sched_day, sched_end) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        user.user_id,
                        currency,
                        value,
                        description,
                        sched_day,
                        sched_end,
                    ),
                )
                sched_expense_id = cursor.lastrowid
                for p in participants:
                    if p["user_id"] == user.user_id:
                        continue
                    conn.execute(
                        "INSERT INTO scheduled_expense_user "
                        "(sched_expense_id, from_user_id, to_user_id, value) "
                        "VALUES (?, ?, ?, ?)",
                        (sched_expense_id, user.user_id, p["user_id"], p["share"]),
                    )
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error creating scheduled expense")
