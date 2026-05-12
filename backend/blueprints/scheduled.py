from datetime import date, datetime

from flask import Blueprint, jsonify, request

from services import login_required, get_session_user
from services.exceptions import UserInputValidationException
from services.scheduled_expense import ScheduledExpenseService
from utils.strings import sanitise

scheduled_bp = Blueprint("scheduled", __name__, url_prefix="/api/scheduled")


@scheduled_bp.post("")
@login_required
def create_scheduled_expense():
    data = request.get_json(silent=True) or {}
    description = sanitise(data.get("description"))
    currency = sanitise(data.get("currency"))
    value = data.get("value")
    participants = data.get("participants")
    sched_day = data.get("sched_day")
    sched_end = data.get("sched_end")

    if not description or not isinstance(description, str):
        raise UserInputValidationException("description is required.")
    if len(currency) == 0:
        raise UserInputValidationException("currency is required.")
    if value is None:
        raise UserInputValidationException("value is required.")
    if not isinstance(value, (int, float)) or value <= 0:
        raise UserInputValidationException("value must be a positive number.")
    if not isinstance(participants, list) or len(participants) == 0:
        raise UserInputValidationException("participants must be a non-empty list.")
    for p in participants:
        if not isinstance(p, dict) or "user_id" not in p or "share" not in p:
            raise UserInputValidationException(
                "Each participant must have user_id and share."
            )
        if not isinstance(p["share"], (int, float)) or p["share"] < 0:
            raise UserInputValidationException(
                "Each participant share must be a positive number."
            )

    if sched_day is None:
        raise UserInputValidationException("sched_day is required.")
    if not isinstance(sched_day, int) or isinstance(sched_day, bool):
        raise UserInputValidationException("sched_day must be an integer.")
    if sched_day < 1 or sched_day > 31:
        raise UserInputValidationException("sched_day must be between 1 and 31.")

    if sched_end is not None:
        if not isinstance(sched_end, str):
            raise UserInputValidationException(
                "sched_end must be a date string in YYYY-MM-DD format."
            )
        try:
            parsed_end = datetime.strptime(sched_end, "%Y-%m-%d").date()
        except ValueError:
            raise UserInputValidationException(
                "sched_end must be a valid date in YYYY-MM-DD format."
            )
        if parsed_end < date.today():
            raise UserInputValidationException("sched_end must not be in the past.")

    user = get_session_user()
    service = ScheduledExpenseService()
    service.create_scheduled_expense(
        user, description, currency, value, participants, sched_day, sched_end
    )

    return jsonify({"message": "Scheduled expense created successfully."}), 201
