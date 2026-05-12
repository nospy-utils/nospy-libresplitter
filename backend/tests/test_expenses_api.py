from base import *
from database import db as db_module

PREFIX = "/api/expenses"
FRIENDS_PREFIX = "/api/friends"


def add_friend(client, email):
    return client.post(FRIENDS_PREFIX, json={"email": email})


def create_expense(
    client, description="Dinner", currency="NZD", value=10.0, participants=None
):
    if participants is None:
        participants = []
    return client.post(
        PREFIX,
        json={
            "description": description,
            "currency": currency,
            "value": value,
            "participants": participants,
        },
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def seed_expense(
    from_user_id, to_user_id, description="lunch", currency="USD", value=10.0
):
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

    def test_empty_activity_when_no_expenses(self, client):
        signup_and_signin(client)

        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 200
        data = r.get_json()
        assert data["activity"] == []
        assert data["total"] == 0
        assert data["has_next"] is False

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
        data = r.get_json()["activity"]
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
        data = r.get_json()["activity"]
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
        seed_expense(
            bob_id, carol_id, description="between others", currency="USD", value=15.0
        )

        signin(client, email="alice@example.com")
        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 200
        assert r.get_json()["activity"] == []

    def test_response_contains_required_fields(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id)

        r = client.get(f"{PREFIX}/activity")
        data = r.get_json()
        for field in ("activity", "total", "page", "page_size", "has_next"):
            assert field in data, f"missing top-level field: {field}"
        row = data["activity"][0]
        for field in (
            "id",
            "from_user_name",
            "is_it_me",
            "description",
            "currency",
            "value",
            "created_at",
        ):
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
        data = r.get_json()["activity"]
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
        descriptions = {row["description"] for row in r.get_json()["activity"]}
        assert descriptions == {"with bob", "with carol"}


# ---------------------------------------------------------------------------
# GET /api/expenses/activity — pagination
# ---------------------------------------------------------------------------


class TestGetActivityPagination:
    def _seed_n(self, alice_id, bob_id, n):
        for i in range(n):
            seed_expense(alice_id, bob_id, description=f"expense-{i}")

    def test_default_pagination_metadata(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id)

        r = client.get(f"{PREFIX}/activity")
        data = r.get_json()
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total"] == 1
        assert data["has_next"] is False

    def test_custom_page_size(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        self._seed_n(alice_id, bob_id, 5)

        r = client.get(f"{PREFIX}/activity?page_size=2")
        data = r.get_json()
        assert len(data["activity"]) == 2
        assert data["page_size"] == 2
        assert data["total"] == 5
        assert data["has_next"] is True

    def test_has_next_false_on_last_page(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        self._seed_n(alice_id, bob_id, 3)

        r = client.get(f"{PREFIX}/activity?page=2&page_size=2")
        data = r.get_json()
        assert len(data["activity"]) == 1
        assert data["has_next"] is False

    def test_second_page_returns_correct_items(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        ids = [
            seed_expense(alice_id, bob_id, description=f"expense-{i}") for i in range(4)
        ]
        # newest first: ids[3], ids[2], ids[1], ids[0]
        # page 1 (size 2): ids[3], ids[2]
        # page 2 (size 2): ids[1], ids[0]

        r = client.get(f"{PREFIX}/activity?page=2&page_size=2")
        rows = r.get_json()["activity"]
        assert len(rows) == 2
        assert rows[0]["id"] == ids[1]
        assert rows[1]["id"] == ids[0]

    def test_page_beyond_total_returns_empty(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id)

        r = client.get(f"{PREFIX}/activity?page=999")
        data = r.get_json()
        assert data["activity"] == []
        assert data["has_next"] is False

    def test_invalid_page_param_returns_400(self, client):
        signup_and_signin(client)

        r = client.get(f"{PREFIX}/activity?page=abc")
        assert r.status_code == 400

    def test_invalid_page_size_param_returns_400(self, client):
        signup_and_signin(client)

        r = client.get(f"{PREFIX}/activity?page_size=xyz")
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/expenses/me
# ---------------------------------------------------------------------------


class TestGetMyExpenses:
    def test_unauthenticated_returns_401(self, client):
        r = client.get(f"{PREFIX}/me")
        assert r.status_code == 401

    def test_empty_result_when_no_expenses(self, client):
        signup_and_signin(client)

        r = client.get(f"{PREFIX}/me")
        assert r.status_code == 200
        data = r.get_json()
        assert data["totals_by_currency"] == []
        assert data["totals_by_friend"] == []

    def test_response_has_required_top_level_keys(self, client):
        signup_and_signin(client)

        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        assert "totals_by_currency" in data
        assert "totals_by_friend" in data

    def test_positive_total_when_user_is_payer(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id, currency="USD", value=30.0)

        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        assert len(data["totals_by_currency"]) == 1
        assert data["totals_by_currency"][0]["currency"] == "USD"
        assert data["totals_by_currency"][0]["my_total"] == 30.0

    def test_negative_total_when_user_is_recipient(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        # Bob paid, Alice owes
        seed_expense(bob_id, alice_id, currency="USD", value=20.0)

        signin(client, email="alice@example.com")
        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        assert data["totals_by_currency"][0]["my_total"] == -20.0

    def test_net_total_aggregates_across_expenses_with_same_friend(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id, currency="USD", value=50.0)  # alice is owed 50
        seed_expense(bob_id, alice_id, currency="USD", value=20.0)  # alice owes 20

        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        assert data["totals_by_currency"][0]["my_total"] == 30.0

        friend = data["totals_by_friend"][0]
        assert friend["friend_name"] == "bob"
        assert friend["currencies"][0]["net_total"] == 30.0

    def test_totals_by_friend_structure(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id, currency="USD", value=10.0)

        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        friend = data["totals_by_friend"][0]
        assert "friend_id" in friend
        assert "friend_name" in friend
        assert "currencies" in friend
        assert len(friend["currencies"]) == 1
        assert "currency" in friend["currencies"][0]
        assert "net_total" in friend["currencies"][0]

    def test_multiple_currencies_appear_in_totals_by_currency(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id, currency="USD", value=10.0)
        seed_expense(alice_id, bob_id, currency="EUR", value=5.0)

        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        currencies = {row["currency"] for row in data["totals_by_currency"]}
        assert currencies == {"USD", "EUR"}

    def test_multiple_currencies_grouped_under_friend(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id, currency="USD", value=10.0)
        seed_expense(alice_id, bob_id, currency="EUR", value=5.0)

        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        assert len(data["totals_by_friend"]) == 1
        friend = data["totals_by_friend"][0]
        assert friend["friend_name"] == "bob"
        currencies = {c["currency"] for c in friend["currencies"]}
        assert currencies == {"USD", "EUR"}

    def test_multiple_friends_appear_separately_in_totals_by_friend(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")
        signup(client, name="carol", email="carol@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="carol@example.com")
        carol_id = get_user_id(client, "carol@example.com")

        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id, currency="USD", value=10.0)
        seed_expense(alice_id, carol_id, currency="USD", value=20.0)

        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        assert len(data["totals_by_friend"]) == 2
        names = {f["friend_name"] for f in data["totals_by_friend"]}
        assert names == {"bob", "carol"}

    def test_excludes_expenses_not_involving_user(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")
        signup(client, name="carol", email="carol@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="carol@example.com")
        carol_id = get_user_id(client, "carol@example.com")

        # Expense only between bob and carol — alice is not involved
        seed_expense(bob_id, carol_id, currency="USD", value=15.0)

        signin(client, email="alice@example.com")
        r = client.get(f"{PREFIX}/me")
        data = r.get_json()
        assert data["totals_by_currency"] == []
        assert data["totals_by_friend"] == []


# ---------------------------------------------------------------------------
# GET /api/expenses/friend/<friend_id>
# ---------------------------------------------------------------------------


class TestGetExpensesWithFriend:
    def test_unauthenticated_returns_401(self, client):
        r = client.get(f"{PREFIX}/friend/1")
        assert r.status_code == 401

    def test_nonexistent_friend_id_returns_404(self, client):
        signup_and_signin(client)

        r = client.get(f"{PREFIX}/friend/9999")
        assert r.status_code == 404

    def test_not_friends_returns_400(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.status_code == 400

    def test_empty_list_when_friends_but_no_expenses(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["friend_name"] == "bob"
        assert data["expenses"] == []

    def test_response_contains_friend_name(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.status_code == 200
        assert r.get_json()["friend_name"] == "bob"

    def test_from_user_name_is_you_when_current_user_paid(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(alice_id, bob_id, description="dinner")

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.status_code == 200
        expenses = r.get_json()["expenses"]
        assert len(expenses) == 1
        assert expenses[0]["from_user_name"] == "You"

    def test_from_user_name_is_friend_name_when_friend_paid(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(bob_id, alice_id, description="coffee")

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.status_code == 200
        expenses = r.get_json()["expenses"]
        assert len(expenses) == 1
        assert expenses[0]["from_user_name"] == "bob"

    def test_response_contains_required_fields(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(alice_id, bob_id, description="lunch", currency="USD", value=12.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        data = r.get_json()
        assert "friend_name" in data
        assert "expenses" in data
        row = data["expenses"][0]
        for field in (
            "id",
            "from_user_name",
            "description",
            "currency",
            "value",
            "created_at",
        ):
            assert field in row, f"missing field: {field}"

    def test_returns_expenses_from_both_directions(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(alice_id, bob_id, description="alice paid")
        seed_expense(bob_id, alice_id, description="bob paid")

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.status_code == 200
        descriptions = {row["description"] for row in r.get_json()["expenses"]}
        assert descriptions == {"alice paid", "bob paid"}

    def test_ordered_newest_first(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        first_id = seed_expense(alice_id, bob_id, description="first")
        second_id = seed_expense(alice_id, bob_id, description="second")

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        expenses = r.get_json()["expenses"]
        assert expenses[0]["id"] == second_id
        assert expenses[1]["id"] == first_id

    def test_excludes_expenses_not_involving_the_friend(self, client):
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
        seed_expense(alice_id, bob_id, description="with bob")
        seed_expense(alice_id, carol_id, description="with carol")

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        expenses = r.get_json()["expenses"]
        assert len(expenses) == 1
        assert expenses[0]["description"] == "with bob"

    def test_correct_values_returned(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(alice_id, bob_id, description="pizza", currency="EUR", value=42.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        row = r.get_json()["expenses"][0]
        assert row["description"] == "pizza"
        assert row["currency"] == "EUR"
        assert row["value"] == 42.0


# ---------------------------------------------------------------------------
# GET /api/expenses/friend/<friend_id> — totals_by_currency
# ---------------------------------------------------------------------------


class TestGetExpensesWithFriendTotalsByCurrency:
    def _setup_alice_and_bob(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        return alice_id, bob_id

    def test_totals_by_currency_present_in_response(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.status_code == 200
        assert "totals_by_currency" in r.get_json()

    def test_totals_by_currency_empty_when_no_expenses(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.get_json()["totals_by_currency"] == []

    def test_totals_by_currency_single_entry_when_alice_paid(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        seed_expense(alice_id, bob_id, currency="USD", value=30.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        totals = r.get_json()["totals_by_currency"]
        assert len(totals) == 1
        assert totals[0]["currency"] == "USD"
        assert totals[0]["net_total"] == 30.0

    def test_totals_by_currency_negative_when_friend_paid(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        seed_expense(bob_id, alice_id, currency="USD", value=20.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        totals = r.get_json()["totals_by_currency"]
        assert len(totals) == 1
        assert totals[0]["net_total"] == -20.0

    def test_totals_by_currency_net_across_multiple_expenses(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        seed_expense(alice_id, bob_id, currency="USD", value=50.0)
        seed_expense(bob_id, alice_id, currency="USD", value=20.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        totals = r.get_json()["totals_by_currency"]
        assert len(totals) == 1
        assert totals[0]["net_total"] == 30.0

    def test_totals_by_currency_separate_entry_per_currency(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        seed_expense(alice_id, bob_id, currency="USD", value=10.0)
        seed_expense(alice_id, bob_id, currency="EUR", value=5.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        totals = r.get_json()["totals_by_currency"]
        assert len(totals) == 2
        currencies = {t["currency"] for t in totals}
        assert currencies == {"USD", "EUR"}

    def test_totals_by_currency_entry_structure(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        seed_expense(alice_id, bob_id, currency="USD", value=10.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        entry = r.get_json()["totals_by_currency"][0]
        for field in ("friend_id", "friend_name", "currency", "net_total"):
            assert field in entry, f"missing field: {field}"

    def test_totals_by_currency_zero_balance_excluded(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        seed_expense(alice_id, bob_id, currency="USD", value=20.0)
        seed_expense(bob_id, alice_id, currency="USD", value=20.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        totals = r.get_json()["totals_by_currency"]
        assert totals == []

    def test_totals_by_currency_only_includes_this_friend(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        signup(client, name="carol", email="carol@example.com")

        signin(client, email="carol@example.com")
        carol_id = get_user_id(client, "carol@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "carol@example.com")
        seed_expense(alice_id, bob_id, currency="USD", value=10.0)
        seed_expense(alice_id, carol_id, currency="USD", value=99.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        totals = r.get_json()["totals_by_currency"]
        assert len(totals) == 1
        assert totals[0]["net_total"] == 10.0


# ---------------------------------------------------------------------------
# GET /api/expenses/friend/<user_id>/settleup
# ---------------------------------------------------------------------------


class TestGetSettleUp:
    def test_unauthenticated_returns_401(self, client):
        r = client.get(f"{PREFIX}/friend/1/settleup")
        assert r.status_code == 401

    def test_nonexistent_user_id_returns_404(self, client):
        signup_and_signin(client)

        r = client.get(f"{PREFIX}/friend/9999/settleup")
        assert r.status_code == 404

    def test_not_friends_returns_400(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert r.status_code == 400

    def test_empty_when_no_expenses(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_returns_amount_when_current_user_owes_friend(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        # Bob paid, alice owes bob
        seed_expense(bob_id, alice_id, currency="USD", value=40.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 1
        assert data[0]["net_total"] == -40.0
        assert data[0]["currency"] == "USD"

    def test_response_contains_required_fields(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(bob_id, alice_id, currency="USD", value=10.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        row = r.get_json()[0]
        for field in ("friend_id", "friend_name", "currency", "net_total"):
            assert field in row, f"missing field: {field}"

    def test_friend_name_and_id_are_correct(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(bob_id, alice_id, currency="USD", value=10.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        row = r.get_json()[0]
        assert row["friend_id"] == bob_id
        assert row["friend_name"] == "bob"

    def test_net_total_aggregates_across_multiple_expenses(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(bob_id, alice_id, currency="USD", value=30.0)
        seed_expense(bob_id, alice_id, currency="USD", value=20.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 1
        assert data[0]["net_total"] == -50.0

    def test_net_amount_when_expenses_go_both_ways(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(bob_id, alice_id, currency="USD", value=50.0)  # alice owes 50
        seed_expense(
            alice_id, bob_id, currency="USD", value=20.0
        )  # alice is owed 20 — net: alice owes 30

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 1
        assert data[0]["net_total"] == -30.0

    def test_separate_entry_per_currency(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(bob_id, alice_id, currency="USD", value=40.0)
        seed_expense(bob_id, alice_id, currency="EUR", value=15.0)

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data) == 2
        currencies = {row["currency"] for row in data}
        assert currencies == {"USD", "EUR"}


# ---------------------------------------------------------------------------
# POST /api/expenses/friend/<user_id>/settleup
# ---------------------------------------------------------------------------


class TestPostSettleUp:
    def _settle(self, client, user_id, currency="USD", value=20.0, reverse=False):
        return client.post(
            f"{PREFIX}/friend/{user_id}/settleup",
            json={"currency": currency, "value": value, "reverse": reverse},
        )

    def test_unauthenticated_returns_401(self, client):
        r = client.post(f"{PREFIX}/friend/1/settleup", json={})
        assert r.status_code == 401

    def test_nonexistent_user_id_returns_404(self, client):
        signup_and_signin(client)

        r = self._settle(client, 9999)
        assert r.status_code == 404

    def test_not_friends_returns_400(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        r = self._settle(client, bob_id)
        assert r.status_code == 400

    def test_missing_currency_returns_400(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        r = client.post(
            f"{PREFIX}/friend/{bob_id}/settleup", json={"value": 10.0, "reverse": False}
        )
        assert r.status_code == 400

    def test_missing_value_returns_400(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        r = client.post(
            f"{PREFIX}/friend/{bob_id}/settleup",
            json={"currency": "USD", "reverse": False},
        )
        assert r.status_code == 400

    def test_non_positive_value_returns_400(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        r = client.post(
            f"{PREFIX}/friend/{bob_id}/settleup",
            json={"currency": "USD", "value": 0, "reverse": False},
        )
        assert r.status_code == 400

    def test_invalid_reverse_type_returns_400(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        r = client.post(
            f"{PREFIX}/friend/{bob_id}/settleup",
            json={"currency": "USD", "value": 10.0, "reverse": "yes"},
        )
        assert r.status_code == 400

    def test_success_returns_201(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")

        r = self._settle(client, bob_id, currency="USD", value=30.0, reverse=False)
        assert r.status_code == 201

    def test_reverse_false_current_user_is_payer(self, client):
        """reverse=False: current user paid the friend — activity shows 'You' as payer."""
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        self._settle(client, bob_id, currency="USD", value=20.0, reverse=False)

        r = client.get(f"{PREFIX}/activity")
        rows = r.get_json()["activity"]
        settle_rows = [row for row in rows if row["description"] == "Settled up"]
        assert len(settle_rows) == 1
        assert settle_rows[0]["is_it_me"] == 1

    def test_reverse_true_friend_is_payer(self, client):
        """reverse=True: friend paid the current user — activity shows friend as payer."""
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        self._settle(client, bob_id, currency="USD", value=20.0, reverse=True)

        r = client.get(f"{PREFIX}/activity")
        rows = r.get_json()["activity"]
        settle_rows = [row for row in rows if row["description"] == "Settled up"]
        assert len(settle_rows) == 1
        assert settle_rows[0]["is_it_me"] == 0
        assert settle_rows[0]["from_user_name"] == "bob"

    def test_settle_up_zeroes_balance(self, client):
        """After settling, net balance for that currency should be 0."""
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        seed_expense(bob_id, alice_id, currency="USD", value=40.0)  # alice owes bob 40

        self._settle(
            client, bob_id, currency="USD", value=40.0, reverse=False
        )  # alice pays bob 40

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert r.status_code == 200
        data = r.get_json()
        usd = next((row for row in data if row["currency"] == "USD"), None)
        assert usd is None or usd["net_total"] == 0.0

    def test_settle_up_recorded_with_correct_currency_and_value(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        self._settle(client, bob_id, currency="EUR", value=55.0, reverse=False)

        r = client.get(f"{PREFIX}/activity")
        rows = r.get_json()["activity"]
        settle_rows = [row for row in rows if row["description"] == "Settled up"]
        assert len(settle_rows) == 1
        assert settle_rows[0]["value"] == 55.0


# ---------------------------------------------------------------------------
# POST /api/expenses
# ---------------------------------------------------------------------------


class TestCreateExpense:
    def _setup_alice_and_bob(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        return alice_id, bob_id

    def _setup_alice_bob_carol(self, client):
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

    # --- authentication ---

    def test_unauthenticated_returns_401(self, client):
        r = client.post(PREFIX, json={})
        assert r.status_code == 401

    # --- input validation (blueprint) ---

    def test_missing_description_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX, json={"currency": "NZD", "value": 10.0, "participants": []}
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
            },
        )
        assert r.status_code == 400

    def test_missing_currency_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX, json={"description": "Dinner", "value": 10.0, "participants": []}
        )
        assert r.status_code == 400

    def test_non_string_currency_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Dinner",
                "currency": 42,
                "value": 10.0,
                "participants": [],
            },
        )
        assert r.status_code == 400

    def test_missing_value_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={"description": "Dinner", "currency": "NZD", "participants": []},
        )
        assert r.status_code == 400

    def test_non_positive_value_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX,
            json={
                "description": "Dinner",
                "currency": "NZD",
                "value": 0,
                "participants": [],
            },
        )
        assert r.status_code == 400

    def test_missing_participants_returns_400(self, client):
        signup_and_signin(client)
        r = client.post(
            PREFIX, json={"description": "Dinner", "currency": "NZD", "value": 10.0}
        )
        assert r.status_code == 400

    def test_empty_participants_returns_400(self, client):
        signup_and_signin(client)
        r = create_expense(client, participants=[])
        assert r.status_code == 400

    def test_participant_missing_user_id_returns_400(self, client):
        signup_and_signin(client)
        r = create_expense(client, participants=[{"share": 10.0}])
        assert r.status_code == 400

    def test_participant_missing_share_returns_400(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        r = create_expense(client, participants=[{"user_id": alice_id}])
        assert r.status_code == 400

    def test_participant_non_positive_share_returns_400(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        r = create_expense(client, participants=[{"user_id": alice_id, "share": -1.0}])
        assert r.status_code == 400

    def test_participant_pay_zero_returns_200(self, client):
        signup_and_signin(client)
        bob_id = get_user_id(client, "bob@example.com")
        #  in this case, bob is supposed to pay for the whole expense
        r = create_expense(
            client,
            participants=[
                {"user_id": bob_id, "share": 10.0},
            ],
        )
        assert r.status_code == 201

    # --- business rule validation (service) ---

    def test_current_user_not_in_participants_returns_400(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        r = create_expense(
            client, value=10.0, participants=[{"user_id": bob_id, "share": 10.0}]
        )
        assert r.status_code == 400

    def test_shares_not_summing_to_value_returns_400(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        r = create_expense(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 4.0},
                {"user_id": bob_id, "share": 4.0},
            ],
        )
        assert r.status_code == 400

    def test_participant_not_a_friend_returns_400(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        # No add_friend call — they are not friends
        r = create_expense(
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
        r = create_expense(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": 9999, "share": 5.0},
            ],
        )
        assert r.status_code == 404

    # --- success cases ---

    def test_success_returns_201(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        r = create_expense(
            client,
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
        )
        assert r.status_code == 201

    def test_expense_appears_in_activity(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        create_expense(
            client,
            description="Pizza",
            currency="NZD",
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 5.0},
                {"user_id": bob_id, "share": 5.0},
            ],
        )

        r = client.get(f"{PREFIX}/activity")
        assert r.status_code == 200
        descriptions = [row["description"] for row in r.get_json()["activity"]]
        assert "Pizza" in descriptions

    def test_expense_appears_in_expenses_with_friend(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        create_expense(
            client,
            description="Groceries",
            currency="NZD",
            value=20.0,
            participants=[
                {"user_id": alice_id, "share": 10.0},
                {"user_id": bob_id, "share": 10.0},
            ],
        )

        r = client.get(f"{PREFIX}/friend/{bob_id}")
        assert r.status_code == 200
        descriptions = [row["description"] for row in r.get_json()["expenses"]]
        assert "Groceries" in descriptions

    def test_three_participants_success(self, client):
        alice_id, bob_id, carol_id = self._setup_alice_bob_carol(client)
        r = create_expense(
            client,
            value=9.0,
            participants=[
                {"user_id": alice_id, "share": 3.0},
                {"user_id": bob_id, "share": 3.0},
                {"user_id": carol_id, "share": 3.0},
            ],
        )
        assert r.status_code == 201

    def test_three_participants_both_friends_appear_in_activity(self, client):
        alice_id, bob_id, carol_id = self._setup_alice_bob_carol(client)
        create_expense(
            client,
            description="Dinner",
            value=9.0,
            participants=[
                {"user_id": alice_id, "share": 3.0},
                {"user_id": bob_id, "share": 3.0},
                {"user_id": carol_id, "share": 3.0},
            ],
        )

        r = client.get(f"{PREFIX}/activity")
        rows = r.get_json()["activity"]
        dinner_rows = [row for row in rows if row["description"] == "Dinner"]
        # Two expense_user rows: alice→bob and alice→carol
        assert len(dinner_rows) == 2

    def test_friend_share_reflected_in_balance(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        create_expense(
            client,
            currency="NZD",
            value=10.0,
            participants=[
                {"user_id": alice_id, "share": 6.0},
                {"user_id": bob_id, "share": 4.0},
            ],
        )

        r = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert r.status_code == 200
        data = r.get_json()
        nzd = next(row for row in data if row["currency"] == "NZD")
        assert nzd["net_total"] == 4.0


class TestDeleteExpense:
    def _setup_alice_and_bob(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")

        signin(client, email="alice@example.com")
        add_friend(client, "bob@example.com")
        return alice_id, bob_id

    def _create_expense_and_get_id(self, client, alice_id, bob_id):
        """Create an expense and return its ID by checking the activity."""
        create_expense(
            client,
            "Test expense",
            "USD",
            20.0,
            [{"user_id": alice_id, "share": 10.0}, {"user_id": bob_id, "share": 10.0}],
        )

        # Get the expense ID from activity
        response = client.get(f"{PREFIX}/activity")
        return response.json["activity"][0]["id"]

    def test_unauthenticated_returns_401(self, client):
        client.post("/api/users/logout")
        response = client.delete(f"{PREFIX}/123")
        assert response.status_code == 401

    def test_nonexistent_expense_returns_404(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        response = client.delete(f"{PREFIX}/99999")
        assert response.status_code == 404

    def test_expense_not_owned_by_user_returns_404(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        expense_id = self._create_expense_and_get_id(client, alice_id, bob_id)

        # Log in as Bob (who didn't create the expense)
        signin(client, email="bob@example.com")

        response = client.delete(f"{PREFIX}/{expense_id}")
        assert response.status_code == 404

    def test_successful_deletion_returns_200(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        expense_id = self._create_expense_and_get_id(client, alice_id, bob_id)

        response = client.delete(f"{PREFIX}/{expense_id}")
        assert response.status_code == 200
        assert response.json["message"] == "Expense deleted successfully."

    def test_deleted_expense_removed_from_activity(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        expense_id = self._create_expense_and_get_id(client, alice_id, bob_id)

        # Verify expense exists in activity
        response = client.get(f"{PREFIX}/activity")
        assert response.json["total"] == 1

        # Delete the expense
        client.delete(f"{PREFIX}/{expense_id}")

        # Verify expense is removed from activity
        response = client.get(f"{PREFIX}/activity")
        assert response.json["total"] == 0
        assert len(response.json["activity"]) == 0

    def test_deleted_expense_removed_from_expenses_with_friend(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        expense_id = self._create_expense_and_get_id(client, alice_id, bob_id)

        # Verify expense exists in expenses with friend
        response = client.get(f"{PREFIX}/friend/{bob_id}")
        assert response.json["total"] == 1

        # Delete the expense
        client.delete(f"{PREFIX}/{expense_id}")

        # Verify expense is removed from expenses with friend
        response = client.get(f"{PREFIX}/friend/{bob_id}")
        assert response.json["total"] == 0
        assert len(response.json["expenses"]) == 0

    def test_deleted_expense_updates_balances(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        expense_id = self._create_expense_and_get_id(client, alice_id, bob_id)

        # Verify initial balance
        response = client.get(f"{PREFIX}/me")
        assert len(response.json["totals_by_friend"]) == 1
        assert (
            response.json["totals_by_friend"][0]["currencies"][0]["net_total"] == 10.0
        )

        # Delete the expense
        client.delete(f"{PREFIX}/{expense_id}")

        # Verify balance is updated (should be empty now)
        response = client.get(f"{PREFIX}/me")
        assert len(response.json["totals_by_friend"]) == 0

    def test_deleted_expense_updates_settle_up_amount(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        expense_id = self._create_expense_and_get_id(client, alice_id, bob_id)

        # Verify initial settle up amount
        response = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert len(response.json) == 1
        assert response.json[0]["net_total"] == 10.0

        # Delete the expense
        client.delete(f"{PREFIX}/{expense_id}")

        # Verify settle up amount is updated (should be empty now)
        response = client.get(f"{PREFIX}/friend/{bob_id}/settleup")
        assert len(response.json) == 0

    def test_deleting_already_deleted_expense_returns_404(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)
        expense_id = self._create_expense_and_get_id(client, alice_id, bob_id)

        # Delete the expense first time
        response = client.delete(f"{PREFIX}/{expense_id}")
        assert response.status_code == 200

        # Try to delete again
        response = client.delete(f"{PREFIX}/{expense_id}")
        assert response.status_code == 404

    def test_delete_one_of_multiple_expenses(self, client):
        alice_id, bob_id = self._setup_alice_and_bob(client)

        # Create two expenses
        create_expense(
            client,
            "First expense",
            "USD",
            20.0,
            [{"user_id": alice_id, "share": 10.0}, {"user_id": bob_id, "share": 10.0}],
        )
        create_expense(
            client,
            "Second expense",
            "USD",
            30.0,
            [{"user_id": alice_id, "share": 15.0}, {"user_id": bob_id, "share": 15.0}],
        )

        # Get expense IDs from activity (newest first)
        response = client.get(f"{PREFIX}/activity")
        expense_ids = [expense["id"] for expense in response.json["activity"]]
        assert len(expense_ids) == 2

        # Delete the first (newest) expense
        client.delete(f"{PREFIX}/{expense_ids[0]}")

        # Verify only one expense remains
        response = client.get(f"{PREFIX}/activity")
        assert response.json["total"] == 1
        assert response.json["activity"][0]["description"] == "First expense"
