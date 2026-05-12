from decimal import Decimal, ROUND_HALF_UP

from daos.scheduled_expense import ScheduledExpenseDAO
from models import User
from services.exceptions import (
    UserInputValidationException,
)
from services.friend import FriendService
from services.user import UserService


class ScheduledExpenseService:

    def __init__(self):
        self.scheduled_expense_dao = ScheduledExpenseDAO()

    def create_scheduled_expense(
        self,
        user: User,
        description,
        currency,
        value,
        participants,
        sched_day,
        sched_end,
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

        self.scheduled_expense_dao.create_scheduled_expense(
            user,
            description.strip(),
            currency.strip(),
            float(value),
            participants,
            int(sched_day),
            sched_end,
        )

    def retrieve_scheduled_expenses(self) -> list:
        return self.scheduled_expense_dao.get_due_scheduled_expenses()
