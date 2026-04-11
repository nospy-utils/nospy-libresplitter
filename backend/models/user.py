from werkzeug.security import generate_password_hash

class User(object):

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

    def generate_password_hash(self) -> str:
        return generate_password_hash(self.password)