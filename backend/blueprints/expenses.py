from flask import Blueprint, jsonify

from services import ExpenseService, login_required, get_session_user

expenses_bp = Blueprint("expenses", __name__, url_prefix="/api/expenses")


@expenses_bp.get("/me")
@login_required
def get_my_expenses():
    user = get_session_user()
    service = ExpenseService()
    data = service.get_my_expenses(user)
    return jsonify(data), 200


@expenses_bp.get("/activity")
@login_required
def get_activity():
    user = get_session_user()
    service = ExpenseService()
    data = service.get_activity(user)
    return jsonify(data), 200
