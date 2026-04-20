from base import *
from database import db as db_module

PREFIX = "/api/friends"


def seed_expense(from_user_id, to_user_id, description="lunch", currency="USD", value=10.0):
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
# POST /api/friends
# ---------------------------------------------------------------------------

class TestAddFriend:
    def test_unauthenticated_returns_401(self, client):
        r = client.post(PREFIX, json={"email": "bob@example.com"})
        assert r.status_code == 401

    def test_success_returns_201(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        r = client.post(PREFIX, json={"email": "bob@example.com"})
        assert r.status_code == 201
        assert "added" in r.get_json()["message"].lower()

    def test_friend_not_found_returns_404(self, client):
        signup_and_signin(client)

        r = client.post(PREFIX, json={"email": "ghost@example.com"})
        assert r.status_code == 404

    def test_add_self_returns_400(self, client):
        signup_and_signin(client)

        r = client.post(PREFIX, json={"email": "alice@example.com"})
        assert r.status_code == 400
        assert "yourself" in r.get_json()["description"].lower()

    def test_duplicate_friend_returns_409(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        client.post(PREFIX, json={"email": "bob@example.com"})
        r = client.post(PREFIX, json={"email": "bob@example.com"})
        assert r.status_code == 409

    def test_missing_email_returns_400(self, client):
        signup_and_signin(client)

        r = client.post(PREFIX, json={})
        assert r.status_code == 400

    def test_email_lookup_is_case_insensitive(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")

        r = client.post(PREFIX, json={"email": "BOB@EXAMPLE.COM"})
        assert r.status_code == 201

    def test_friendship_is_not_duplicated_when_added_from_both_sides(self, client):
        """Adding B→A after A→B is already set must return 409, not create a second row."""
        signup_and_signin(client, name="alice", email="alice@example.com")
        signup(client, name="bob", email="bob@example.com")

        client.post(PREFIX, json={"email": "bob@example.com"})

        # Switch to bob's session
        client.post(f"{USERS_PREFIX}/signout")
        signin(client, email="bob@example.com")

        r = client.post(PREFIX, json={"email": "alice@example.com"})
        assert r.status_code == 409


# ---------------------------------------------------------------------------
# GET /api/friends/recent
# ---------------------------------------------------------------------------

class TestGetRecentFriends:
    def test_unauthenticated_returns_401(self, client):
        r = client.get(f"{PREFIX}/recent")
        assert r.status_code == 401

    def test_empty_result_when_no_interactions(self, client):
        signup_and_signin(client)
        r = client.get(f"{PREFIX}/recent")
        assert r.status_code == 200
        body = r.get_json()
        assert body["friends"] == []
        assert body["total"] == 0

    def test_returns_friend_after_shared_expense(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")
        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")
        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id)

        r = client.get(f"{PREFIX}/recent")
        assert r.status_code == 200
        friends = r.get_json()["friends"]
        assert len(friends) == 1
        assert friends[0]["id"] == bob_id
        assert friends[0]["name"] == "bob"

    def test_response_has_pagination_fields(self, client):
        signup_and_signin(client)
        r = client.get(f"{PREFIX}/recent")
        body = r.get_json()
        for key in ("friends", "total", "page", "page_size", "has_next"):
            assert key in body

    def test_ordered_by_most_recent_interaction(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")
        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")
        signup(client, name="carol", email="carol@example.com")
        signin(client, email="carol@example.com")
        carol_id = get_user_id(client, "carol@example.com")
        signin(client, email="alice@example.com")

        seed_expense(alice_id, carol_id, description="older")
        seed_expense(alice_id, bob_id, description="newer")

        r = client.get(f"{PREFIX}/recent")
        friends = r.get_json()["friends"]
        assert friends[0]["id"] == bob_id
        assert friends[1]["id"] == carol_id

    def test_custom_page_size(self, client):
        signup_and_signin(client)
        alice_id = get_user_id(client, "alice@example.com")
        signup(client, name="bob", email="bob@example.com")
        signin(client, email="bob@example.com")
        bob_id = get_user_id(client, "bob@example.com")
        signup(client, name="carol", email="carol@example.com")
        signin(client, email="carol@example.com")
        carol_id = get_user_id(client, "carol@example.com")
        signin(client, email="alice@example.com")
        seed_expense(alice_id, bob_id)
        seed_expense(alice_id, carol_id)

        r = client.get(f"{PREFIX}/recent?page_size=1")
        body = r.get_json()
        assert len(body["friends"]) == 1
        assert body["has_next"] is True

    def test_invalid_page_param_returns_400(self, client):
        signup_and_signin(client)
        r = client.get(f"{PREFIX}/recent?page=abc")
        assert r.status_code == 400
