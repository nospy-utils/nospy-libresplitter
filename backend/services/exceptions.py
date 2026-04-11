from werkzeug.exceptions import HTTPException


class UserInputValidationException(HTTPException):

    code = 400

    def __init__(self, description: str):
        super().__init__(description)
