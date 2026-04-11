from models import User

from daos import UserDAO
from services.exceptions import UserInputValidationException


class UserService:

    def save_user(self, name:str, email:str, password:str) -> None:
        user = User(
            name=name,
            email=email,
            password=password
        )

        if not name or not email or not password:
            raise UserInputValidationException('Name, Email and password are required')

        if len(password) < 8:
            raise UserInputValidationException('Password must be at least 8 characters.')

        dao = UserDAO()
        dao.save_user(user)
