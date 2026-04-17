from typing import Any

from daos import ExpenseDAO
from models import User
from services.exceptions import NotFriendsException
from services.friend import FriendService
from services.user import UserService
from utils.pagination import Page


class ExpenseService:

    def __init__(self):
        self.expense_dao = ExpenseDAO()

    def get_expenses_with_friend(self, user: User, friend_id: int, page: Page) -> dict:
        friend = UserService().get_user_by_id(friend_id)
        if not FriendService().are_friends(user, friend):
            raise NotFriendsException()

        result = self.expense_dao.get_expenses_with_friend(user, friend_id, page)
        return {"friend_name": friend.name, **result}

    def get_settle_up_amount(self, user: User, friend_id: int) -> list:
        friend = UserService().get_user_by_id(friend_id)
        if not FriendService().are_friends(user, friend):
            raise NotFriendsException()

        return self.expense_dao.get_settle_up_amount(user, friend_id)

    def settle_up(self, user: User, friend_id: int, currency: str, value: float, reverse: bool) -> None:
        friend = UserService().get_user_by_id(friend_id)
        if not FriendService().are_friends(user, friend):
            raise NotFriendsException()

        self.expense_dao.create_settle_up(user, friend, currency, value, reverse)

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
