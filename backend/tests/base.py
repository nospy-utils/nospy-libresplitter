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