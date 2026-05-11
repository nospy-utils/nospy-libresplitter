from werkzeug.security import check_password_hash

from models import User

from daos import UserDAO
from services.exceptions import (
    UserInputValidationException,
    InvalidCredentialsException,
    UserNotFoundException,
)


class UserService:

    def __init__(self):
        self.user_dao = UserDAO()

    def authenticate(self, email: str, password: str) -> User:
        if not email or not password:
            raise UserInputValidationException("Email and password are required.")

        row = self.user_dao.find_by_email(email)

        if row is None or not check_password_hash(row["password"], password):
            raise InvalidCredentialsException()

        user = User(
            user_id=row["id"],
            name=row["name"],
            email=row["email"],
        )

        return user

    def get_user_by_id(self, user_id: int) -> User:
        row = self.user_dao.find_by_id(user_id)
        if row is None:
            raise UserNotFoundException()
        return User(user_id=row["id"], name=row["name"], email=row["email"])

    def find_by_email(self, user_email: str) -> User:
        row = self.user_dao.find_by_email(user_email)
        if row is None:
            raise UserNotFoundException()
        return User(user_id=row["id"], name=row["name"], email=row["email"])

    def save_user(self, name: str, email: str, password: str) -> None:
        user = User(name=name, email=email, password=password)

        if not name or not email or not password:
            raise UserInputValidationException("Name, Email and password are required")

        if len(password) < 8:
            raise UserInputValidationException(
                "Password must be at least 8 characters."
            )

        self.user_dao.save_user(user)
