import json
import os

from werkzeug.exceptions import HTTPException
from flask import Flask
from flask_cors import CORS


from database.db import init_db
from blueprints import users_bp, friends_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

cors = CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
], "supports_credentials": True}})

init_db()

app.register_blueprint(users_bp)
app.register_blueprint(friends_bp)

@app.errorhandler(HTTPException)
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
