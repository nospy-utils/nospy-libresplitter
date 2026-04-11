import json
import os

import werkzeug
from flask import Flask

from db import init_db
from blueprints import users_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

init_db()

app.register_blueprint(users_bp)

@app.errorhandler(werkzeug.exceptions.HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

if __name__ == "__main__":
    app.run(debug=True, port=5000)
