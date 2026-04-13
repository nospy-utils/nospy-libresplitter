from werkzeug.security import generate_password_hash

class User(object):

    def __init__(self, user_id:int = None, name:str = None, email:str = None, password:str = None):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password

    def generate_password_hash(self) -> str:
        return generate_password_hash(self.password)

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented

        return (self.user_id == other.user_id and
                self.name == other.name and
                self.email == other.email)