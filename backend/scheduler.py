from apscheduler.schedulers.background import BackgroundScheduler

from services.expense import ExpenseService
from services.scheduled_expense import ScheduledExpenseService
from services.user import UserService

scheduler: BackgroundScheduler | None = None


def add_recurrent_expenses(app):
    scheduled_service = ScheduledExpenseService()
    expense_service = ExpenseService()
    user_service = UserService()

    due = scheduled_service.retrieve_scheduled_expenses()
    app.logger.info("Found %d scheduled expense(s) due today", len(due))

    created = 0
    for sched in due:
        try:
            creator = user_service.get_user_by_id(sched["user_created"])
            expense_service.create_expense(
                creator,
                sched["description"],
                sched["currency"],
                sched["value"],
                sched["participants"],
            )
            created += 1
        except Exception as e:
            # Don't let a single bad row halt the whole batch.
            app.logger.exception(
                "Failed to materialise scheduled expense id=%s: %s",
                sched.get("id"),
                e,
            )

    app.logger.info("Materialised %d/%d scheduled expense(s)", created, len(due))


def init_scheduler(app):
    global scheduler

    if scheduler is None:
        app.logger.info("Initializing scheduler")
        scheduler = BackgroundScheduler()
        scheduler.add_job(add_recurrent_expenses, args=[app], trigger="cron", hour=1)
        # scheduler.add_job(add_recurrent_expenses, args=[app], trigger='interval', seconds=10)
        scheduler.start()
