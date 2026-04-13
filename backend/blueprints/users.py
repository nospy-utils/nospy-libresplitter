from flask import Blueprint, request, jsonify, session

from services import UserService, login_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

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

    service = UserService()
    user = service.authenticate(email, password)

    session.permanent = remember
    session["user_id"] = user.user_id
    session["name"] = user.name
    session["email"] = user.email

    return jsonify({"message": "Signed in successfully."}), 200


@users_bp.post("/signout")
@login_required
def signout():
    session.clear()
    return jsonify({"message": "Signed out successfully."}), 200


@users_bp.get("/me")
@login_required
def me():
    return jsonify({"user_id": session["user_id"], "email": session["email"]}), 200
