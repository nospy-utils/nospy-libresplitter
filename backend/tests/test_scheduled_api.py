from datetime import date, timedelta

from base import *
from database import db as db_module

PREFIX = "/api/scheduled"
FRIENDS_PREFIX = "/api/friends"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def add_friend(client, email):
    return client.post(FRIENDS_PREFIX, json={"email": email})


def create_scheduled(
    client,
    description="Rent",
    currency="NZD",
    value=100.0,
    participants=None,
    sched_day=1,
    sched_end=None,
):
    if participants is None:
        participants = []
    payload = {
        "description": description,
        "currency": currency,
        "value": value,
        "participants": participants,
        "sched_day": sched_day,
    }
    if sched_end is not None:
        payload["sched_end"] = sched_end
    return client.post(PREFIX, json=payload)


def _setup_alice_and_bob(client):
    signup_and_signin(client)
    alice_id = get_user_id(client, "alice@example.com")
    signup(client, name="bob", email="bob@example.com")

    signin(client, email="bob@example.com")
    bob_id = get_user_id(client, "bob@example.com")

    signin(client, email="alice@example.com")
    add_friend(client, "bob@example.com")
    return alice_id, bob_id


def _setup_alice_bob_carol(client):
    signup_and_signin(client)
    alice_id = get_user_id(client, "alice@example.com")
    signup(client, name="bob", email="bob@example.com")
    signup(client, name="carol", email="carol@example.com")

    signin(client, email="bob@example.com")
    bob_id = get_user_id(client, "bob@example.com")

    signin(client, email="carol@example.com")
    carol_id = get_user_id(client, "carol@example.com")

    signin(client, email="alice@example.com")
    add_friend(client, "bob@example.com")
    add_friend(client, "carol@example.com")
    return alice_id, bob_id, carol_id


# ---------------------------------------------------------------------------
# POST /api/scheduled
# ---------------------------------------------------------------------------


class TestCreateScheduledExpense:

    # --- authentication ---

    def test_unauthenticated_returns_401(self, client):
        r = client.post(PREFIX, json={})
        assert r.status_code == 401

    # --- input validation: shared with create_expense ---

    def test_missing_description_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "currency": "NZD",
                "value": 10.0,
                "participants": [],
                "sched_day": 1,
            },
        )
        assert r.status_code == 400

    def test_non_string_description_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "description": 123,
                "currency": "NZD",
                "value": 10.0,
                "participants": [],
                "sched_day": 1,
            },
        )
        assert r.status_code == 400

    def test_missing_currency_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Rent",
                "value": 10.0,
                "participants": [],
                "sched_day": 1,
            },
        )
        assert r.status_code == 400

    def test_non_string_currency_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Rent",
                "currency": 42,
                "value": 10.0,
                "participants": [],
                "sched_day": 1,
            },
        )
        assert r.status_code == 400

    def test_missing_value_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Rent",
                "currency": "NZD",
                "participants": [],
                "sched_day": 1,
            },
        )
        assert r.status_code == 400

    def test_non_positive_value_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Rent",
                "currency": "NZD",
                "value": 0,
                "participants": [],
                "sched_day": 1,
            },
        )
        assert r.status_code == 400

    def test_missing_participants_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Rent",
                "currency": "NZD",
                "value": 10.0,
                "sched_day": 1,
            },
        )
        assert r.status_code == 400

    def test_empty_participants_returns_400(self, client):
        signup_and_signin(client)
        r = create_scheduled(client, participants=[])
        assert r.status_code == 400

    def test_participant_missing_user_id_returns_400(self, client):
        signup_and_signin(client)
        r = create_scheduled(client, participants=[{"share": 10.0}])
        assert r.status_code == 400

    def test_participant_missing_share_returns_400(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        r = create_scheduled(client, participants=[{"user_id": alice_id}])
        assert r.status_code == 400

    def test_participant_non_positive_share_returns_400(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        r = create_scheduled(
            client, participants=[{"user_id": alice_id, "share": -1.0}]
        )
        assert r.status_code == 400

    def test_current_user_not_in_participants_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[{"user_id": bob_id, "share": 10.0}],
        )
        assert r.status_code == 400

    def test_shares_not_summing_to_value_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 4.0},
                {"user_id": bob_id, "share": 4.0},
            ],
        )
        assert r.status_code == 400

    def test_participant_not_a_friend_returns_400(self, client):
        # alice signed in, but bob is NOT added as a friend
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
        )
        assert r.status_code == 400

    def test_nonexistent_participant_returns_404(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": 99999, "share": 5.0},
            ],
        )
        assert r.status_code == 404

    # --- input validation: scheduled-specific ---

    def test_missing_sched_day_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Rent",
                "currency": "NZD",
                "value": 10.0,
                "participants": [
                    {"user_id": alice_id, "share": 5.0},
                    {"user_id": bob_id, "share": 5.0},
                ],
            },
        )
        assert r.status_code == 400

    def test_non_integer_sched_day_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day="first",
        )
        assert r.status_code == 400

    def test_boolean_sched_day_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=True,
        )
        assert r.status_code == 400

    def test_sched_day_zero_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=0,
        )
        assert r.status_code == 400

    def test_sched_day_too_large_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=32,
        )
        assert r.status_code == 400

    def test_invalid_sched_end_format_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=1,
            sched_end="not-a-date",
        )
        assert r.status_code == 400

    def test_non_string_sched_end_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=1,
            sched_end=20251231,
        )
        assert r.status_code == 400

    def test_sched_end_in_the_past_returns_400(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        past = (date.today() - timedelta(days=1)).isoformat()
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=1,
            sched_end=past,
        )
        assert r.status_code == 400

    # --- success cases ---

    def test_success_returns_201(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            description="Rent",
            currency="NZD",
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=1,
        )
        assert r.status_code == 201
        assert "message" in r.get_json()

    def test_success_with_sched_end_returns_201(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        future = (date.today() + timedelta(days=365)).isoformat()
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=15,
            sched_end=future,
        )
        assert r.status_code == 201

    def test_success_with_null_sched_end_returns_201(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Rent",
                "currency": "NZD",
                "value": 10.0,
                "participants": [
                    {"user_id": alice_id, "share": 5.0},
                    {"user_id": bob_id, "share": 5.0},
                ],
                "sched_day": 1,
                "sched_end": None,
            },
        )
        assert r.status_code == 201

    def test_three_participants_success(self, client):
        alice_id, bob_id, carol_id = _setup_alice_bob_carol(client)
        r = create_scheduled(
            client,
            value=30.0,
            participants=[
                {"user_id": alice_id, "share": 10.0},
                {"user_id": bob_id, "share": 10.0},
                {"user_id": carol_id, "share": 10.0},
            ],
            sched_day=10,
        )
        assert r.status_code == 201

    # --- persistence checks ---

    def _get_scheduled_row(self, scheduled_id):
        with db_module.get_db() as conn:
            row = conn.execute(
                "SELECT * FROM scheduled_expenses WHERE id = ?", (scheduled_id,)
            ).fetchone()
            return dict(row) if row else None

    def _get_scheduled_user_rows(self, scheduled_id):
        with db_module.get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_expense_user WHERE sched_expense_id = ?",
                (scheduled_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def test_scheduled_expense_persisted_to_db(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            description="Rent",
            currency="NZD",
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=7,
        )
        assert r.status_code == 201

        with db_module.get_db() as conn:
            rows = conn.execute("SELECT * FROM scheduled_expenses").fetchall()
        assert len(rows) == 1
        row = dict(rows[0])
        assert row["user_created"] == alice_id
        assert row["currency"] == "NZD"
        assert row["value"] == 10.0
        assert row["description"] == "Rent"
        assert row["sched_day"] == 7
        assert row["sched_end"] is None

    def test_scheduled_expense_persists_sched_end(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        future = (date.today() + timedelta(days=30)).isoformat()
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=15,
            sched_end=future,
        )
        assert r.status_code == 201

        with db_module.get_db() as conn:
            row = conn.execute(
                "SELECT sched_day, sched_end FROM scheduled_expenses"
            ).fetchone()
        assert row["sched_day"] == 15
        assert row["sched_end"] == future

    def test_scheduled_expense_user_rows_created_for_friends_only(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=1,
        )
        assert r.status_code == 201

        with db_module.get_db() as conn:
            sched_id = conn.execute("SELECT id FROM scheduled_expenses").fetchone()[
                "id"
            ]

        rows = self._get_scheduled_user_rows(sched_id)
        # Only one row: alice -> bob (alice is the creator and is excluded)
        assert len(rows) == 1
        assert rows[0]["from_user_id"] == alice_id
        assert rows[0]["to_user_id"] == bob_id
        assert rows[0]["value"] == 5.0

    def test_three_participants_persisted_correctly(self, client):
        alice_id, bob_id, carol_id = _setup_alice_bob_carol(client)
        r = create_scheduled(
            client,
            value=30.0,
            participants=[
                {"user_id": alice_id, "share": 10.0},
                {"user_id": bob_id, "share": 10.0},
                {"user_id": carol_id, "share": 10.0},
            ],
            sched_day=20,
        )
        assert r.status_code == 201

        with db_module.get_db() as conn:
            sched_id = conn.execute("SELECT id FROM scheduled_expenses").fetchone()[
                "id"
            ]

        rows = self._get_scheduled_user_rows(sched_id)
        # Two rows: alice -> bob, alice -> carol
        assert len(rows) == 2
        to_users = sorted(r["to_user_id"] for r in rows)
        assert to_users == sorted([bob_id, carol_id])
        for row in rows:
            assert row["from_user_id"] == alice_id
            assert row["value"] == 10.0

    def test_does_not_create_normal_expense(self, client):
        """Creating a scheduled expense must not create a row in the expenses table."""
        alice_id, bob_id = _setup_alice_and_bob(client)
        r = create_scheduled(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
            sched_day=1,
        )
        assert r.status_code == 201

        with db_module.get_db() as conn:
            count = conn.execute("SELECT COUNT(*) as c FROM expenses").fetchone()["c"]
        assert count == 0


# ---------------------------------------------------------------------------
# ScheduledExpenseService.retrieve_scheduled_expenses
# ---------------------------------------------------------------------------


class TestRetrieveScheduledExpenses:
    """Unit tests for ScheduledExpenseService.retrieve_scheduled_expenses.

    These tests bypass the HTTP layer and exercise the service directly,
    after seeding rows into the SQLite database used by the test client
    fixture.
    """

    @staticmethod
    def _today_day():
        return date.today().day

    @staticmethod
    def _other_day():
        # Pick any day-of-month that is guaranteed not to be "today" and is
        # always a valid day-of-month (1..28).
        today = date.today().day
        return 1 if today != 1 else 2

    @staticmethod
    def _insert_scheduled(
        user_created,
        value,
        sched_day,
        sched_end=None,
        currency="NZD",
        description="Rent",
    ):
        with db_module.get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO scheduled_expenses "
                "(user_created, currency, value, description, sched_day, sched_end) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_created, currency, value, description, sched_day, sched_end),
            )
            return cursor.lastrowid

    @staticmethod
    def _insert_scheduled_user(sched_id, from_user_id, to_user_id, value):
        with db_module.get_db() as conn:
            conn.execute(
                "INSERT INTO scheduled_expense_user "
                "(sched_expense_id, from_user_id, to_user_id, value) "
                "VALUES (?, ?, ?, ?)",
                (sched_id, from_user_id, to_user_id, value),
            )

    def _service(self):
        # Imported lazily so the test-client fixture has had a chance to
        # rebind the DB path before the service touches the database.
        from services.scheduled_expense import ScheduledExpenseService

        return ScheduledExpenseService()

    # --- empty / no-match cases ---

    def test_returns_empty_list_when_no_scheduled_expenses(self, client):
        assert self._service().retrieve_scheduled_expenses() == []

    def test_excludes_scheduled_expenses_not_due_today(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        sched_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._other_day()
        )
        self._insert_scheduled_user(sched_id, alice_id, bob_id, 5.0)

        assert self._service().retrieve_scheduled_expenses() == []

    def test_excludes_scheduled_expenses_past_sched_end(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        past = (date.today() - timedelta(days=1)).isoformat()
        sched_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._today_day(), sched_end=past
        )
        self._insert_scheduled_user(sched_id, alice_id, bob_id, 5.0)

        assert self._service().retrieve_scheduled_expenses() == []

    # --- positive cases ---

    def test_includes_scheduled_expense_due_today_with_null_sched_end(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        sched_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._today_day(), sched_end=None
        )
        self._insert_scheduled_user(sched_id, alice_id, bob_id, 5.0)

        result = self._service().retrieve_scheduled_expenses()
        assert len(result) == 1
        assert result[0]["id"] == sched_id

    def test_includes_scheduled_expense_due_today_with_future_sched_end(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        future = (date.today() + timedelta(days=30)).isoformat()
        sched_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._today_day(), sched_end=future
        )
        self._insert_scheduled_user(sched_id, alice_id, bob_id, 5.0)

        result = self._service().retrieve_scheduled_expenses()
        assert len(result) == 1
        assert result[0]["id"] == sched_id

    def test_includes_scheduled_expense_with_sched_end_equal_to_today(self, client):
        """sched_end IS today should still be considered active (<= comparison)."""
        alice_id, bob_id = _setup_alice_and_bob(client)
        today = date.today().isoformat()
        sched_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._today_day(), sched_end=today
        )
        self._insert_scheduled_user(sched_id, alice_id, bob_id, 5.0)

        result = self._service().retrieve_scheduled_expenses()
        assert len(result) == 1
        assert result[0]["id"] == sched_id

    # --- shape / participants format ---

    def test_returned_fields_include_scheduled_expense_columns(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        sched_id = self._insert_scheduled(
            alice_id,
            value=20.0,
            sched_day=self._today_day(),
            currency="USD",
            description="Internet",
        )
        self._insert_scheduled_user(sched_id, alice_id, bob_id, 10.0)

        result = self._service().retrieve_scheduled_expenses()
        assert len(result) == 1
        row = result[0]
        assert row["id"] == sched_id
        assert row["user_created"] == alice_id
        assert row["currency"] == "USD"
        assert row["value"] == 20.0
        assert row["description"] == "Internet"
        assert row["sched_day"] == self._today_day()
        assert row["sched_end"] is None
        assert "participants" in row

    def test_participants_format_matches_create_expense(self, client):
        """The participants list must use the {"user_id", "share"} shape that
        ExpenseService.create_expense expects, with the creator included so
        the validation `sum(shares) == value` passes."""
        alice_id, bob_id = _setup_alice_and_bob(client)
        sched_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._today_day()
        )
        self._insert_scheduled_user(sched_id, alice_id, bob_id, 4.0)

        result = self._service().retrieve_scheduled_expenses()
        participants = result[0]["participants"]

        # Every participant entry has exactly the expected keys.
        for p in participants:
            assert set(p.keys()) == {"user_id", "share"}

        user_ids = sorted(p["user_id"] for p in participants)
        assert user_ids == sorted([alice_id, bob_id])

        # The shares must sum to the scheduled-expense value.
        total_share = sum(float(p["share"]) for p in participants)
        assert total_share == 10.0

        # The creator must be one of the participants.
        assert any(p["user_id"] == alice_id for p in participants)

        # Bob's share matches what was inserted into scheduled_expense_user.
        bob_entry = next(p for p in participants if p["user_id"] == bob_id)
        assert float(bob_entry["share"]) == 4.0

    def test_participants_for_three_user_scheduled_expense(self, client):
        alice_id, bob_id, carol_id = _setup_alice_bob_carol(client)
        sched_id = self._insert_scheduled(
            alice_id, value=30.0, sched_day=self._today_day()
        )
        self._insert_scheduled_user(sched_id, alice_id, bob_id, 10.0)
        self._insert_scheduled_user(sched_id, alice_id, carol_id, 10.0)

        result = self._service().retrieve_scheduled_expenses()
        assert len(result) == 1
        participants = result[0]["participants"]

        user_ids = sorted(p["user_id"] for p in participants)
        assert user_ids == sorted([alice_id, bob_id, carol_id])

        total_share = sum(float(p["share"]) for p in participants)
        assert total_share == 30.0

    # --- multiple rows ---

    def test_returns_multiple_due_scheduled_expenses(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)
        sched_id_1 = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._today_day(), description="Rent"
        )
        self._insert_scheduled_user(sched_id_1, alice_id, bob_id, 5.0)

        sched_id_2 = self._insert_scheduled(
            alice_id, value=20.0, sched_day=self._today_day(), description="Internet"
        )
        self._insert_scheduled_user(sched_id_2, alice_id, bob_id, 8.0)

        result = self._service().retrieve_scheduled_expenses()
        assert len(result) == 2
        ids = sorted(r["id"] for r in result)
        assert ids == sorted([sched_id_1, sched_id_2])

    def test_only_returns_due_expenses_when_mixed_with_non_due(self, client):
        alice_id, bob_id = _setup_alice_and_bob(client)

        due_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._today_day()
        )
        self._insert_scheduled_user(due_id, alice_id, bob_id, 5.0)

        # Not due today (different day-of-month).
        not_due_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._other_day()
        )
        self._insert_scheduled_user(not_due_id, alice_id, bob_id, 5.0)

        # Due day matches but past sched_end.
        past = (date.today() - timedelta(days=1)).isoformat()
        expired_id = self._insert_scheduled(
            alice_id, value=10.0, sched_day=self._today_day(), sched_end=past
        )
        self._insert_scheduled_user(expired_id, alice_id, bob_id, 5.0)

        result = self._service().retrieve_scheduled_expenses()
        assert len(result) == 1
        assert result[0]["id"] == due_id
