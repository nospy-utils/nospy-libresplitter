from werkzeug.exceptions import HTTPException


class ServiceInternalException(HTTPException):

    code = 500

    def __init__(self, description: str):
        super().__init__(description)