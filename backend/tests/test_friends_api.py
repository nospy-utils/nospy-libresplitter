PREFIX = "/api/friends"
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
# GET /api/friends
# ---------------------------------------------------------------------------

class TestListFriends:
    def test_unauthenticated_returns_401(self, client):
        r = client.get(PREFIX)
        assert r.status_code == 401

    def test_empty_list_when_no_friends(self, client):
        signup_and_signin(client)

        r = client.get(PREFIX)
        assert r.status_code == 200
        assert r.get_json()["friends"] == []

    def test_returns_added_friend(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")
        client.post(PREFIX, json={"email": "bob@example.com"})

        r = client.get(PREFIX)
        assert r.status_code == 200
        friends = r.get_json()["friends"]
        assert len(friends) == 1
        assert friends[0]["email"] == "bob@example.com"
        assert friends[0]["name"] == "bob"
        assert "id" in friends[0]

    def test_friend_sees_relationship_from_their_side(self, client):
        """If alice adds bob, bob's friend list should also include alice."""
        signup_and_signin(client, name="alice", email="alice@example.com")
        signup(client, name="bob", email="bob@example.com")
        client.post(PREFIX, json={"email": "bob@example.com"})

        client.post(f"{USERS_PREFIX}/signout")
        signin(client, email="bob@example.com")

        r = client.get(PREFIX)
        assert r.status_code == 200
        friends = r.get_json()["friends"]
        assert len(friends) == 1
        assert friends[0]["email"] == "alice@example.com"

    def test_returns_multiple_friends(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")
        signup(client, name="carol", email="carol@example.com")
        client.post(PREFIX, json={"email": "bob@example.com"})
        client.post(PREFIX, json={"email": "carol@example.com"})

        r = client.get(PREFIX)
        assert r.status_code == 200
        emails = {f["email"] for f in r.get_json()["friends"]}
        assert emails == {"bob@example.com", "carol@example.com"}

    def test_current_user_not_in_own_friend_list(self, client):
        signup_and_signin(client)
        signup(client, name="bob", email="bob@example.com")
        client.post(PREFIX, json={"email": "bob@example.com"})

        r = client.get(PREFIX)
        emails = [f["email"] for f in r.get_json()["friends"]]
        assert "alice@example.com" not in emails
