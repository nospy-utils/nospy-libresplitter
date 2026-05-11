from typing import Any
from decimal import Decimal, ROUND_HALF_UP

from daos import ExpenseDAO
from models import User
from services.exceptions import (
    NotFriendsException,
    UserInputValidationException,
    ExpenseNotFoundException,
)
from services.friend import FriendService
from services.user import UserService
from utils.pagination import Page


class ExpenseService:

    def __init__(self):
        self.expense_dao = ExpenseDAO()

    def create_expense(
        self, user: User, description, currency, value, participants
    ) -> None:
        participant_ids = [p["user_id"] for p in participants]
        if user.user_id not in participant_ids:
            raise UserInputValidationException(
                "The logged-in user must be one of the participants."
            )

        # damn you IEEE 754
        tmp_sum = Decimal(sum(p["share"] for p in participants)).quantize(
            Decimal("0.00"), rounding=ROUND_HALF_UP
        )
        if float(tmp_sum) != float(value):
            raise UserInputValidationException(
                "Sum of participant shares must equal the expense value."
            )

        friend_service = FriendService()
        user_service = UserService()
        for p in participants:
            if p["user_id"] == user.user_id:
                continue
            participant = user_service.get_user_by_id(p["user_id"])
            if not friend_service.are_friends(user, participant):
                raise UserInputValidationException(
                    f"You are not friends with user {p['user_id']}."
                )

        self.expense_dao.create_expense(
            user, description.strip(), currency.strip(), float(value), participants
        )

    def get_expenses_with_friend(self, user: User, friend_id: int, page: Page) -> dict:
        friend = UserService().get_user_by_id(friend_id)
        if not FriendService().are_friends(user, friend):
            raise NotFriendsException()

        totals_by_currency = self.expense_dao.get_totals_by_friend(user, friend)
        result = self.expense_dao.get_expenses_with_friend(user, friend, page)
        return {
            "friend_name": friend.name,
            "totals_by_currency": totals_by_currency,
            **result,
        }

    def get_settle_up_amount(self, user: User, friend_id: int) -> list:
        friend = UserService().get_user_by_id(friend_id)
        if not FriendService().are_friends(user, friend):
            raise NotFriendsException()

        return self.expense_dao.get_settle_up_amount(user, friend_id)

    def settle_up(
        self, user: User, friend_id: int, currency: str, value: float, reverse: bool
    ) -> None:
        friend = UserService().get_user_by_id(friend_id)
        if not FriendService().are_friends(user, friend):
            raise NotFriendsException()

        self.expense_dao.create_settle_up(user, friend, currency, value, reverse)

    def get_activity(self, user: User, page: Page) -> dict:
        return self.expense_dao.get_activity(user, page)

    def get_my_expenses(self, user: User) -> dict:
        totals_by_currency = self.expense_dao.get_totals_by_currency(user)
        flat_by_friend = self.expense_dao.get_totals_group_by_friend(user)

        totals_by_friend = self._group_by_friend(flat_by_friend)

        return {
            "totals_by_currency": totals_by_currency,
            "totals_by_friend": totals_by_friend,
        }

    def delete_expense(self, user: User, expense_id: int) -> None:
        """Delete an expense if the user owns it."""
        expense_owner_id = self.expense_dao.get_expense_owner(expense_id)

        if expense_owner_id is None:
            raise ExpenseNotFoundException()

        if expense_owner_id != user.user_id:
            raise ExpenseNotFoundException()

        self.expense_dao.delete_expense(expense_id)

    def _group_by_friend(self, flat_by_friend: list) -> list[dict[str, Any]]:
        grouped = {}
        for row in flat_by_friend:
            fid = row["friend_id"]
            if fid not in grouped:
                grouped[fid] = {"friend_name": row["friend_name"], "currencies": []}
            grouped[fid]["currencies"].append(
                {"currency": row["currency"], "net_total": row["net_total"]}
            )

        totals_by_friend = [
            {
                "friend_id": fid,
                "friend_name": data["friend_name"],
                "currencies": data["currencies"],
            }
            for fid, data in grouped.items()
        ]
        return totals_by_friend
