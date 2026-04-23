from werkzeug.exceptions import HTTPException


class UserInputValidationException(HTTPException):

    code = 400

    def __init__(self, description: str):
        super().__init__(description)


class InvalidCredentialsException(HTTPException):

    code = 400

    def __init__(self, description: str = "Invalid email or password."):
        super().__init__(description)

class UserNotAuthenticatedException(HTTPException):

    code = 401

    def __init__(self, description: str = "User is not authenticated."):
        super().__init__(description)


class UserNotFoundException(HTTPException):

    code = 404

    def __init__(self, description: str = "User not found."):
        super().__init__(description)


class FriendAlreadyExistsException(HTTPException):

    code = 409

    def __init__(self, description: str = "Already friends with this user."):
        super().__init__(description)


class NotFriendsException(HTTPException):

    code = 400

    def __init__(self, description: str = "You are not friends with this user."):
        super().__init__(description)

# TODO Maybe I don't want to be as explicit about this one
class ExpenseNotFoundException(HTTPException):

    code = 404

    def __init__(self, description: str = "Expense not found."):
        super().__init__(description)
