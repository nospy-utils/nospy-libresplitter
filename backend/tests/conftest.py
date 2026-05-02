import pytest
import flask_limiter

# Replace Limiter with a no-op before app.py is imported so no storage
# backend (e.g. memcached) is ever initialised during tests.
class _NoOpLimiter:
    def __init__(self, *args, **kwargs): pass
    def __getattr__(self, name): return lambda *a, **kw: None
    def limit(self, *args, **kwargs):
        return lambda f: f
    def exempt(self, f):
        return f

flask_limiter.Limiter = _NoOpLimiter

from database import db as db_module
from app import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Flask test client wired to an isolated per-test SQLite database.

    app.py calls init_db() at import time against the real DB_PATH, so the
    fixture re-runs init_db() after redirecting DB_PATH to a fresh temp file,
    ensuring each test starts with a clean, empty schema.
    """
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    db_module.init_db()

    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"

    with app.test_client() as c:
        yield c