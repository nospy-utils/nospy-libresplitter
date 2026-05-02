import json
import os

from werkzeug.exceptions import HTTPException
from flask import Flask, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from database.db import init_db
from blueprints import users_bp, friends_bp, expenses_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

cors = CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
], "supports_credentials": True}})

init_db()

# rate limiter
app.config['RATELIMIT_HEADERS_ENABLED'] = True
app.config['RATELIMIT_DEFAULTS_PER_METHOD'] = True

def get_rate_limiter_key() -> str:
    user_id: int | None = session.get('user_id')
    return user_id if user_id else get_remote_address()

limiter = Limiter(
    get_rate_limiter_key,
    app=app,
    default_limits=["10/second"],
    storage_uri=os.environ.get("APP_RL_STORAGE_URI", "memcached://localhost:11211"),
)

app.register_blueprint(users_bp)
app.register_blueprint(friends_bp)
app.register_blueprint(expenses_bp)

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
