from daos import UserDAO, FriendDAO
from models import User
from services import UserService
from services.exceptions import FriendNotFoundException, UserInputValidationException


class FriendService:

    def __init__(self):
        self.user_service = UserService()
        self.friend_dao = FriendDAO()

    def add_friend(self, current_user: User, friend_email: str) -> None:
        friend_email = (friend_email or "").strip().lower()
        if not friend_email:
            raise UserInputValidationException("Email is required.")

        friend = self.user_service.find_by_email(friend_email)

        if current_user == friend:
            raise UserInputValidationException("You cannot add yourself as a friend.")

        self.friend_dao.add_friend(current_user, friend)

    def list_friends(self, current_user_id: User) -> list:
        return self.friend_dao.list_friends(current_user_id)
