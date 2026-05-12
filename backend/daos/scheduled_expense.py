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

    def get_due_scheduled_expenses(self) -> list:
        try:
            with get_db() as conn:
                sched_rows = conn.execute("""
                    SELECT
                        id,
                        user_created,
                        currency,
                        value,
                        description,
                        created_at,
                        sched_day,
                        sched_end
                    FROM scheduled_expenses
                    WHERE (sched_end IS NULL OR date('now') <= sched_end)
                      AND sched_day = CAST(strftime('%d', 'now') AS INTEGER)
                    """).fetchall()

                results = []
                for row in sched_rows:
                    sched = dict(row)
                    participant_rows = conn.execute(
                        """
                        SELECT from_user_id, to_user_id, value
                        FROM scheduled_expense_user
                        WHERE sched_expense_id = ?
                        """,
                        (sched["id"],),
                    ).fetchall()

                    participants = []
                    creator_id = sched["user_created"]
                    creator_share = 0.0
                    for p in participant_rows:
                        participants.append(
                            {"user_id": p["to_user_id"], "share": p["value"]}
                        )
                        creator_share += float(p["value"])

                    # The creator is always one of the participants in the
                    # shape that ExpenseService.create_expense expects.
                    creator_remaining = float(sched["value"]) - creator_share
                    participants.append(
                        {"user_id": creator_id, "share": creator_remaining}
                    )

                    sched["participants"] = participants
                    results.append(sched)

                return results
        except sqlite3.OperationalError as e:
            logger.exception(e)
            raise ServiceUnavailableException("Service Unavailable")
        except sqlite3.DatabaseError as e:
            logger.exception(e)
            raise ServiceInternalException("Error fetching due scheduled expenses")
