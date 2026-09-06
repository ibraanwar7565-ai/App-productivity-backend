"""Tests for auth flow, user-owned notes, protection, and pagination."""

import os
os.environ["DATABASE_URI"] = "sqlite:///:memory:"

import pytest

from app import app, db
from models import User, Note


@pytest.fixture(autouse=True)
def app_context():
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def signup(client, username="alice", password="secret"):
    return client.post("/signup", json={"username": username, "password": password})


# ---------- Auth ----------

def test_signup_creates_user(client):
    resp = signup(client)
    assert resp.status_code == 201
    assert resp.get_json()["username"] == "alice"


def test_signup_requires_fields(client):
    assert client.post("/signup", json={"username": "x"}).status_code == 422


def test_signup_unique_username(client):
    signup(client)
    with client.session_transaction() as s:
        s["user_id"] = None
    assert signup(client).status_code == 422


def test_password_is_protected(client):
    signup(client)
    user = User.query.filter_by(username="alice").first()
    with pytest.raises(AttributeError):
        user.password_hash
    assert user.authenticate("secret")


def test_login_and_logout(client):
    signup(client)
    with client.session_transaction() as s:
        s["user_id"] = None
    assert client.post("/login", json={"username": "alice", "password": "secret"}).status_code == 200
    assert client.post("/login", json={"username": "alice", "password": "wrong"}).status_code == 401
    assert client.delete("/logout").status_code == 204


def test_check_session(client):
    assert client.get("/check_session").status_code == 401
    signup(client)
    assert client.get("/check_session").status_code == 200


# ---------- Notes CRUD + protection + pagination ----------

def test_notes_require_auth(client):
    assert client.get("/notes").status_code == 401
    assert client.post("/notes", json={"title": "x"}).status_code == 401


def test_note_crud(client):
    signup(client)
    created = client.post("/notes", json={"title": "Buy milk", "category": "errands"})
    assert created.status_code == 201
    nid = created.get_json()["id"]
    assert client.get(f"/notes/{nid}").status_code == 200
    patched = client.patch(f"/notes/{nid}", json={"title": "Buy oat milk"})
    assert patched.get_json()["title"] == "Buy oat milk"
    assert client.delete(f"/notes/{nid}").status_code == 200
    assert client.get(f"/notes/{nid}").status_code == 404


def test_note_invalid_returns_422(client):
    signup(client)
    assert client.post("/notes", json={"title": ""}).status_code == 422


def test_pagination(client):
    signup(client)
    for i in range(12):
        client.post("/notes", json={"title": f"Note {i}"})
    resp = client.get("/notes?page=1&per_page=5")
    data = resp.get_json()
    assert data["total"] == 12
    assert data["per_page"] == 5
    assert data["total_pages"] == 3
    assert len(data["items"]) == 5


def test_users_only_see_their_own_notes(client):
    # Alice creates a note
    signup(client, "alice", "secret")
    note = client.post("/notes", json={"title": "Alice private"}).get_json()
    client.delete("/logout")

    # Bob logs in and must not access Alice's note
    signup(client, "bob", "secret")
    assert client.get(f"/notes/{note['id']}").status_code == 404
    # Bob's own index is empty
    assert client.get("/notes").get_json()["total"] == 0
