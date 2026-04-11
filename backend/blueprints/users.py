from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash

from db import get_db
from services import UserService

users_bp = Blueprint("users", __name__, url_prefix="/api")


@users_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}

    name = data.get("name") or ""
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    service = UserService()
    service.save_user(name, email, password)

    return jsonify({"message": "Account created successfully."}), 201


@users_bp.post("/signin")
def signin():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    remember = bool(data.get("remember_me", False))

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    with get_db() as conn:
        row = conn.execute(
            "SELECT id, email, password FROM users WHERE email = ?", (email,)
        ).fetchone()

    if row is None or not check_password_hash(row["password"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    session.permanent = remember
    session["user_id"] = row["id"]
    session["email"] = row["email"]

    return jsonify({"message": "Signed in successfully.", "email": row["email"]}), 200


@users_bp.post("/signout")
def signout():
    session.clear()
    return jsonify({"message": "Signed out successfully."}), 200


@users_bp.get("/me")
def me():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated."}), 401
    return jsonify({"user_id": session["user_id"], "email": session["email"]}), 200
