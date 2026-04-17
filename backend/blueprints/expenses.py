from flask import Blueprint, jsonify, request

from services import ExpenseService, login_required, get_session_user
from services.exceptions import UserInputValidationException
from utils.pagination import validate_pagination_request_params

expenses_bp = Blueprint("expenses", __name__, url_prefix="/api/expenses")


@expenses_bp.get("/me")
@login_required
def get_my_expenses():
    user = get_session_user()
    service = ExpenseService()
    data = service.get_my_expenses(user)
    return jsonify(data), 200


@expenses_bp.get("/friend/<int:friend_id>")
@login_required
def get_expenses_with_friend(friend_id):
    pagination = validate_pagination_request_params(request)
    user = get_session_user()
    service = ExpenseService()
    data = service.get_expenses_with_friend(user, friend_id, pagination)
    return jsonify(data), 200


@expenses_bp.get("/friend/<int:user_id>/settleup")
@login_required
def get_settle_up_amount(user_id):
    user = get_session_user()
    service = ExpenseService()
    data = service.get_settle_up_amount(user, user_id)
    return jsonify(data), 200


@expenses_bp.post("/friend/<int:user_id>/settleup")
@login_required
def settle_up(user_id):
    data = request.get_json(silent=True) or {}
    currency = data.get("currency") or ""
    value = data.get("value")
    reverse = data.get("reverse")

    if not currency:
        raise UserInputValidationException("currency is required.")
    if value is None:
        raise UserInputValidationException("value is required.")
    if not isinstance(value, (int, float)) or value <= 0:
        raise UserInputValidationException("value must be a positive number.")
    if not isinstance(reverse, bool):
        raise UserInputValidationException("reverse must be a boolean.")

    user = get_session_user()
    service = ExpenseService()
    service.settle_up(user, user_id, currency, float(value), reverse)

    return jsonify({"message": "Settled up successfully."}), 201


@expenses_bp.get("/activity")
@login_required
def get_activity():
    user = get_session_user()
    service = ExpenseService()
    data = service.get_activity(user)
    return jsonify(data), 200
