from flask import Blueprint, request, jsonify

from services import FriendService, UserService, login_required, get_session_user
from utils.pagination import validate_pagination_request_params

friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")


@friends_bp.get("/recent")
@login_required
def get_recent_friends():
    pagination = validate_pagination_request_params(request)
    user = get_session_user()
    service = FriendService()
    data = service.get_recent_friends(user, pagination)
    return jsonify(data), 200


@friends_bp.post("")
@login_required
def add_friend():
    data = request.get_json(silent=True) or {}
    friend_email = data.get("email") or ""

    user = get_session_user()
    service = FriendService()
    service.add_friend(user, friend_email)

    return jsonify({"message": "Friend added successfully."}), 201


