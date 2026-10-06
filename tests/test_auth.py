import pytest
from jsonschema import validate

from framework import factories, schemas
from framework.config import PASSWORD


@pytest.mark.smoke
def test_register_creates_a_customer_and_logs_in(anon):
    email = factories.unique_email()
    res = anon.post("auth/register", json={"email": email, "password": PASSWORD})

    assert res.status_code == 201
    user = res.json()["user"]
    validate(user, schemas.USER)
    assert user["email"] == email and user["role"] == "user"
    assert anon.get("auth/me").status_code == 200  # the session cookie was issued


def test_duplicate_registration_is_rejected(anon, user):
    res = anon.post("auth/register", json={"email": user.email, "password": PASSWORD})
    assert res.status_code == 400
    assert res.json()["message"] == "User already exists"


@pytest.mark.parametrize("body", [
    {},
    {"email": "a@example.com"},
    {"password": PASSWORD},
    {"email": "", "password": PASSWORD},
    {"email": "not-an-email", "password": PASSWORD},
    {"email": 123, "password": PASSWORD},
])
def test_registration_rejects_invalid_input(anon, body):
    assert anon.post("auth/register", json=body).status_code == 400


@pytest.mark.smoke
def test_login_returns_the_user_and_starts_a_session(anon, user):
    res = anon.post("auth/login", json={"email": user.email, "password": user.password})
    assert res.status_code == 200
    assert res.json()["user"]["id"] == user.id
    assert anon.get("auth/me").json()["user"]["email"] == user.email


def test_wrong_password_and_unknown_email_give_the_same_answer(anon, user):
    wrong = anon.post("auth/login", json={"email": user.email, "password": "nope"})
    unknown = anon.post("auth/login", json={"email": factories.unique_email(), "password": "nope"})
    assert wrong.status_code == unknown.status_code == 400
    assert wrong.json() == unknown.json()  # no user enumeration


def test_me_requires_a_session(anon):
    assert anon.get("auth/me").status_code == 401


def test_logout_ends_the_session(user):
    assert user.api.post("auth/logout").status_code == 200
    assert user.api.get("auth/me").status_code == 401
