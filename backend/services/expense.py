from typing import Any

from daos import ExpenseDAO
from models import User


class ExpenseService:

    def __init__(self):
        self.expense_dao = ExpenseDAO()

    def get_activity(self, user: User) -> list:
        return self.expense_dao.get_activity(user)

    def get_my_expenses(self, user: User) -> dict:
        totals_by_currency = self.expense_dao.get_totals_by_currency(user)
        flat_by_friend = self.expense_dao.get_totals_by_friend(user)

        totals_by_friend = self._group_by_friend(flat_by_friend)

        return {
            "totals_by_currency": totals_by_currency,
            "totals_by_friend": totals_by_friend,
        }

    def _group_by_friend(self, flat_by_friend: list) -> list[dict[str, Any]]:
        grouped = {}
        for row in flat_by_friend:
            fid = row["friend_id"]
            if fid not in grouped:
                grouped[fid] = {"friend_name": row["friend_name"], "currencies": []}
            grouped[fid]["currencies"].append({"currency": row["currency"], "net_total": row["net_total"]})

        totals_by_friend = [
            {"friend_id": fid, "friend_name": data["friend_name"], "currencies": data["currencies"]}
            for fid, data in grouped.items()
        ]
        return totals_by_friend
