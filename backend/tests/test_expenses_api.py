import pytest

from database import db as db_module

PREFIX = "/api/expenses"
USERS_PREFIX = "/api/users"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def signup(client, name="alice", email="alice@example.com", password="password123"):
    return client.post(
        f"{USERS_PREFIX}/signup",
        json={"name": name, "email": email, "password": password},
    )


def signin(client, email="alice@example.com", password="password123"):
    return client.post(
        f"{USERS_PREFIX}/signin",
        json={"email": email, "password": password},
    )


def signup_and_signin(client, name="alice", email="alice@example.com", password="password123"):
    signup(client, name=name, email=email, password=password)
    signin(client, email=email, password=password)


def get_user_id(client, email):
    """Return the numeric user id for a signed-in user."""
    r = client.get(f"{USERS_PREFIX}/me")
    return r.get_json()["user_id"]


def seed_expense(from_user_id, to_user_id, description="lunch", currency="USD", value=10.0):
    """Insert one expense + one expense_user row directly into the test DB."""
    with db_module.get_db() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (user_created, currency, value, description) VALUES (?, ?, ?, ?)",
            (from_user_id, currency, value, description),
        )
        expense_id = cur.lastrowid
        conn.execute(
            "INSERT INTO expense_user (expense_id, from_user_id, to_user_id, value) VALUES (?, ?, ?, ?)",
            (expense_id, from_user_id, to_user_id, value),
        )
        return expense_id


# ---------------------------------------------------------------------------
# GET /api/expenses/activity
# ---------------------------------------------------------------------------

class TestGetActivity:
    def test_unauthenticated_returns_401(self, client):
        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 401

    def test_empty_list_when_no_expenses(self, client):
        signup_and_signin(client)

        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_returns_expense_where_user_is_payer(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id, description="dinner", currency="USD", value=20.0)

        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 1
        assert data[0]["from_user_name"] == "alice"
        assert data[0]["is_it_me"] == 1
        assert data[0]["description"] == "dinner"
        assert data[0]["currency"] == "USD"
        assert data[0]["value"] == 20.0

    def test_returns_expense_where_user_is_recipient(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        # Bob pays, Alice receives — from_user_name should be bob's name
        seed_expense(bob_id, alice_id, description="coffee", currency="USD", value=5.0)

        signin(client, email="alice@example.com")
        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 1
        assert data[0]["from_user_name"] == "bob"
        assert data[0]["is_it_me"] == 0

    def test_excludes_expenses_not_involving_user(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")
        signup(client, name="carol", email="carol@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="carol@example.com")
        carol_id = get_user_id(client, "carol@example.com")

        # Expense between bob and carol — alice is not involved
        seed_expense(bob_id, carol_id, description="between others", currency="USD", value=15.0)

        signin(client, email="alice@example.com")
        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_response_contains_required_fields(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id)

        r = client.get(f"{PREFIX}/activity")
        row = r.get_json()[0]
        for field in ("id", "from_user_name", "is_it_me", "description", "currency", "value", "created_at"):
            assert field in row, f"missing field: {field}"

    def test_ordered_newest_first(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        first_id = seed_expense(alice_id, bob_id, description="first", value=5.0)
        second_id = seed_expense(alice_id, bob_id, description="second", value=10.0)

        r = client.get(f"{PREFIX}/activity")
        data = r.get_json()
        assert data[0]["id"] == second_id
        assert data[1]["id"] == first_id

    def test_returns_all_expenses_involving_user(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")
        signup(client, name="carol", email="carol@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="carol@example.com")
        carol_id = get_user_id(client, "carol@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id, description="with bob")
        seed_expense(carol_id, alice_id, description="with carol")
        # unrelated expense
        seed_expense(bob_id, carol_id, description="bob and carol")

        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 200
        descriptions = {row["description"] for row in r.get_json()}
        assert descriptions == {"with bob", "with carol"}
