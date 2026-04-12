# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PREFIX = "/api/users"

def signup(client, name="user", email="user@example.com", password="password123"):
    return client.post(
        f"{PREFIX}/signup",
        json={"name": name, "email": email, "password": password},
    )


def signin(client, email="user@example.com", password="password123", remember_me=False):
    return client.post(
        f"{PREFIX}/signin",
        json={"email": email, "password": password, "remember_me": remember_me},
    )

class TestSignup:
    def test_success_returns_201(self, client):
        r = signup(client)
        assert r.status_code == 201
        assert "created" in r.get_json()["message"].lower()

    def test_duplicate_email_returns_500(self, client):
        signup(client)
        r = signup(client)
        assert r.status_code == 500
        assert "error saving user" in r.get_json()["description"].lower()

    def test_email_is_case_insensitive(self, client):
        signup(client, email="User@Example.COM")
        r = signup(client, email="user@example.com")
        assert r.status_code == 500

    def test_missing_email_returns_400(self, client):
        r = client.post(f"{PREFIX}/signup", json={"password": "password123"})
        assert r.status_code == 400

    def test_missing_password_returns_400(self, client):
        r = client.post(f"{PREFIX}/signup", json={"email": "user@example.com"})
        assert r.status_code == 400

    def test_empty_body_returns_400(self, client):
        r = client.post(f"{PREFIX}/signup", json={})
        assert r.status_code == 400

    def test_non_json_body_returns_400(self, client):
        r = client.post(f"{PREFIX}/signup", data="not-json", content_type="text/plain")
        assert r.status_code == 400

    def test_password_too_short_returns_400(self, client):
        r = signup(client, password="short")
        assert r.status_code == 400
        assert "8 characters" in r.get_json()["description"]

    def test_password_exactly_8_chars_is_accepted(self, client):
        r = signup(client, password="12345678")
        assert r.status_code == 201


class TestSignin:
    def test_success_returns_200_with_email(self, client):
        signup(client)
        r = signin(client)
        assert r.status_code == 200

    def test_wrong_password_returns_401(self, client):
        signup(client)
        r = signin(client, password="wrongpassword")
        assert r.status_code == 401
        assert "invalid email or password" in r.get_json()["description"].lower()

    def test_unknown_email_returns_401(self, client):
        r = signin(client, email="ghost@example.com")
        assert r.status_code == 401
        assert "invalid email or password" in r.get_json()["description"].lower()

    def test_missing_email_returns_400(self, client):
        r = client.post(f"{PREFIX}/signin", json={"password": "password123"})
        assert r.status_code == 400
        assert "required" in r.get_json()["description"].lower()

    def test_missing_password_returns_400(self, client):
        r = client.post(f"{PREFIX}/signin", json={"email": "user@example.com"})
        assert r.status_code == 400
        assert "required" in r.get_json()["description"].lower()

    def test_signin_email_is_case_insensitive(self, client):
        signup(client, email="user@example.com")
        r = signin(client, email="USER@EXAMPLE.COM")
        assert r.status_code == 200

    def test_sets_session_on_success(self, client):
        signup(client)
        signin(client)
        r = client.get(f"{PREFIX}/me")
        assert r.status_code == 200
        assert r.get_json()["email"] == "user@example.com"

    def test_remember_me_false_does_not_make_session_permanent(self, client):
        signup(client)
        with client.session_transaction() as sess:
            pass  # open session context
        signin(client, remember_me=False)
        with client.session_transaction() as sess:
            assert not sess.permanent

    def test_remember_me_true_makes_session_permanent(self, client):
        signup(client)
        signin(client, remember_me=True)
        with client.session_transaction() as sess:
            assert sess.permanent


class TestSignout:
    def test_signout_clears_session(self, client):
        signup(client)
        signin(client)
        client.post(f"{PREFIX}/signout")
        r = client.get(f"{PREFIX}/me")
        assert r.status_code == 401

    def test_signout_returns_200(self, client):
        r = client.post(f"{PREFIX}/signout")
        assert r.status_code == 200

    def test_signout_without_session_still_returns_200(self, client):
        r = client.post(f"{PREFIX}/signout")
        assert r.status_code == 200


class TestMe:
    def test_unauthenticated_returns_401(self, client):
        r = client.get(f"{PREFIX}/me")
        assert r.status_code == 401

    def test_authenticated_returns_user_info(self, client):
        signup(client)
        signin(client)
        r = client.get(f"{PREFIX}/me")
        assert r.status_code == 200
        body = r.get_json()
        assert body["email"] == "user@example.com"
        assert "user_id" in body

    def test_after_signout_returns_401(self, client):
        signup(client)
        signin(client)
        client.post(f"{PREFIX}/signout")
        r = client.get(f"{PREFIX}/me")
        assert r.status_code == 401
