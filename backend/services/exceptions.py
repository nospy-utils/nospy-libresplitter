from werkzeug.exceptions import HTTPException


class UserInputValidationException(HTTPException):

    code = 400

    def __init__(self, description: str):
        super().__init__(description)


class InvalidCredentialsException(HTTPException):

    code = 401

    def __init__(self, description: str = "Invalid email or password."):
        super().__init__(description)
