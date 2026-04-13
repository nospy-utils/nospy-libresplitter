from flask import Blueprint, request, jsonify

from services import FriendService, UserService, login_required, get_session_user

friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")


@friends_bp.post("")
@login_required
def add_friend():
    data = request.get_json(silent=True) or {}
    friend_email = data.get("email") or ""

    user = get_session_user()
    service = FriendService()
    service.add_friend(user, friend_email)

    return jsonify({"message": "Friend added successfully."}), 201


@friends_bp.get("")
@login_required
def list_friends():
    user = get_session_user()
    service = FriendService()
    friends = service.list_friends(user)

    return jsonify({"friends": friends}), 200
