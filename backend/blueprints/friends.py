from flask import Blueprint, request, jsonify

from services import FriendService, UserService, login_required, get_session_user
from utils.pagination import validate_pagination_request_params
from utils.strings import sanitise

friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")


@friends_bp.get("/recent")
@login_required
def get_recent_friends():
    pagination = validate_pagination_request_params(request)
    user = get_session_user()
    service = FriendService()
    data = service.get_recent_friends(user, pagination)
    return jsonify(data), 200


@friends_bp.get("/<int:user_id>")
@login_required
def get_friend(user_id: int):
    current_user = get_session_user()
    user_service = UserService()
    friend_service = FriendService()

    friend = user_service.get_user_by_id(user_id)
    friend = friend_service.get_friend(current_user, friend)

    return jsonify({"id": friend.user_id, "name": friend.name}), 200


@friends_bp.post("")
@login_required
def add_friend():
    data = request.get_json(silent=True) or {}
    friend_email = sanitise(data.get("email"))

    user = get_session_user()
    service = FriendService()
    service.add_friend(user, friend_email)

    return jsonify({"message": "Friend added successfully."}), 201
