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
